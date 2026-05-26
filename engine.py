import json
import logging
import os
import queue
import subprocess
import sys
import threading
import time
import traceback
from pathlib import Path
from typing import Dict

from constants import ANALYZE_COMMAND, KOMI_KEY, RULE_KEY


def _setup_debug_logger():
  log_path = Path.home() / "light_lizzie_engine_debug.log"
  logger = logging.getLogger("katago_engine_debug")
  logger.setLevel(logging.DEBUG)
  if not logger.handlers:
    handler = logging.FileHandler(log_path, mode="a", encoding="utf-8")
    handler.setFormatter(logging.Formatter(
      "%(asctime)s.%(msecs)03d [%(threadName)s] %(message)s",
      datefmt="%H:%M:%S",
    ))
    logger.addHandler(handler)
  logger.info("=" * 60)
  logger.info("KataGoGTP debug log start (pid=%d, platform=%s, py=%s)",
              os.getpid(), sys.platform, sys.version.split()[0])
  logger.info("log file: %s", log_path)
  return logger


_log = _setup_debug_logger()


class KataGoGTP:
  def __init__(self, exe_path, model_path, config_path):
    # 1. 프로세스 실행
    cmd = [exe_path, "gtp", "-model", model_path, "-config", config_path]
    _log.info("launching: %s", cmd)
    self.process = subprocess.Popen(
      cmd,
      stdin=subprocess.PIPE,
      stdout=subprocess.PIPE,
      stderr=subprocess.PIPE,
      text=True,
      encoding='utf-8',
      errors='replace',
      bufsize=1
    )
    _log.info("subprocess pid=%s", self.process.pid)

    self.last_analysis = ""      # 최신 분석 텍스트 저장
    self.is_running = True
    self.analysis_callback = None # UI 업데이트용 콜백 (선택 사항)
    self.sent_cmd_id = 0
    self.acked_cmd_id = 0
    self.cmd_queue = queue.Queue()
    self.is_waiting = False
    self._wait_started_at = None
    self._info_count = 0
    self._last_info_log = time.time()


    # 2. 엔진 로딩 확인
    time.sleep(1)
    if self.process.poll() is not None:
      error_msg = self.process.stderr.read()
      _log.error("engine exited early: %s", error_msg)
      print(f"엔진 조기 종료 에러:\n{error_msg}")
      return

    # 3. [핵심] 모든 출력을 읽어들일 단 하나의 리스너 스레드 시작
    self.listener_thread = threading.Thread(target=self._listen, name="kata-stdout", daemon=True)
    self.listener_thread.start()
    self.stderr_thread = threading.Thread(target=self._drain_stderr, name="kata-stderr", daemon=True)
    self.stderr_thread.start()
    self.watchdog_thread = threading.Thread(target=self._watchdog, name="kata-watchdog", daemon=True)
    self.watchdog_thread.start()


  def clear_board(self):
    self.send_command("clear_board")


  def set_rule_and_komi(self, rule: str, komi: float):
    self.send_command(f"{RULE_KEY} {rule}")
    self.send_command(f"{KOMI_KEY} {komi}")


  def _drain_stderr(self):
    """katago의 stderr를 비워 Windows 파이프 버퍼(~4KB)가 막히지 않게 함"""
    try:
      while self.is_running and self.process.poll() is None:
        line = self.process.stderr.readline()
        if not line:
          _log.warning("stderr EOF (engine likely exited, returncode=%s)", self.process.poll())
          break
        _log.debug("STDERR: %s", line.rstrip())
    except Exception:
      _log.error("_drain_stderr crashed:\n%s", traceback.format_exc())


  def _watchdog(self):
    """is_waiting이 너무 오래 True 상태이면 행이 의심된다고 기록"""
    WARN_AFTER = 5.0
    last_warn_at = 0.0
    while self.is_running:
      time.sleep(1.0)
      started = self._wait_started_at
      if started is None:
        continue
      stuck_for = time.time() - started
      if stuck_for > WARN_AFTER and (time.time() - last_warn_at) > 5.0:
        _log.warning(
          "WATCHDOG stuck %.1fs: sent=%d acked=%d queue=%d listener_alive=%s stderr_alive=%s engine_alive=%s",
          stuck_for, self.sent_cmd_id, self.acked_cmd_id, self.cmd_queue.qsize(),
          self.listener_thread.is_alive(), self.stderr_thread.is_alive(),
          self.process.poll() is None,
        )
        last_warn_at = time.time()


  def _listen(self):
    """엔진의 stdout을 독점적으로 모니터링하는 스레드 함수"""
    try:
      while self.is_running and self.process.poll() is None:
        line = self.process.stdout.readline()
        if not line:
          _log.warning("stdout EOF (engine likely exited, returncode=%s)", self.process.poll())
          break

        line = line.strip()
        if not line:
          continue

        # 분석 정보(info)인 경우 보관 및 콜백 실행
        if line.startswith("info"):
          self.last_analysis = line
          self._info_count += 1
          now = time.time()
          if now - self._last_info_log > 5.0:
            _log.debug("STDOUT info heartbeat: %d info lines received total", self._info_count)
            self._last_info_log = now
          if self.analysis_callback:
            # 주의: 이 콜백은 리스너 스레드에서 실행됨
            try:
              self.analysis_callback(line)
            except Exception:
              _log.error("analysis_callback raised:\n%s", traceback.format_exc())

        # 일반 응답(=) 처리 (필요 시 로그 출력)
        elif line.startswith("="):
          _log.info("STDOUT response: %r", line[:200])
          rest = line[1:].strip()
          if not rest:
            _log.error("response had no id payload: %r — listener would have died here pre-fix", line)
            continue
          first_tok = rest.split()[0]
          try:
            cmd_id = int(first_tok)
          except ValueError:
            _log.error("could not parse cmd id from %r (first token %r) — pre-fix this killed listener", line, first_tok)
            continue
          _log.info("ACK id=%d  (sent_cmd_id=%d acked_cmd_id_before=%d queue=%d)",
                    cmd_id, self.sent_cmd_id, self.acked_cmd_id, self.cmd_queue.qsize())
          self.acked_cmd_id = cmd_id + 1
          self.is_waiting = False
          self._wait_started_at = None
          self._process_request()
        else:
          _log.debug("STDOUT other: %s", line[:200])
    except Exception:
      _log.error("_listen crashed (this would silently freeze the app):\n%s", traceback.format_exc())


  def send_command(self, command):
    _log.info("send_command(%r) from thread=%s  sent=%d acked=%d waiting=%s queue=%d",
              command, threading.current_thread().name,
              self.sent_cmd_id, self.acked_cmd_id, self.is_waiting, self.cmd_queue.qsize())
    self.cmd_queue.put((self.sent_cmd_id, command))
    self.sent_cmd_id += 1
    self._process_request()


  def _process_request(self):
    caller = threading.current_thread().name
    if self.is_waiting or self.acked_cmd_id == self.sent_cmd_id:
      _log.debug("_process_request skip caller=%s waiting=%s sent=%d acked=%d",
                 caller, self.is_waiting, self.sent_cmd_id, self.acked_cmd_id)
      return
    try:
      id, command = self.cmd_queue.get_nowait()
    except queue.Empty:
      _log.warning("_process_request: queue empty though sent != acked (caller=%s sent=%d acked=%d)",
                   caller, self.sent_cmd_id, self.acked_cmd_id)
      return
    _log.info("STDIN  -> id=%d %s   (caller=%s)", id, command, caller)
    try:
      self.process.stdin.write(f"{id} {command}\n")
      self.process.stdin.flush()
    except Exception:
      _log.error("stdin write failed for %r:\n%s", command, traceback.format_exc())
      return
    if command == ANALYZE_COMMAND:
      self.acked_cmd_id = id + 1
      return self._process_request()
    else:
      self.is_waiting = True
      self._wait_started_at = time.time()


  def play_move(self, color, vertex):
    """한 수를 놓음 (B Q16 등)"""
    self.send_command(f"play {color} {vertex}")


  def undo(self):
    """한 수 무르기"""
    self.send_command("undo")


  def start_analyze(self, callback=None):
    """분석 시작 (콜백 함수를 등록할 수 있음)"""
    self.analysis_callback = callback
    self.send_command(ANALYZE_COMMAND)


  def stop_analyze(self):
    """분석 중단"""
    # GTP에서 아무 명령이나 보내면 분석이 중단됨
    self.send_command("stop")
    self.analysis_callback = None


  def close(self):
    """엔진 종료"""
    _log.info("close() called")
    self.is_running = False
    if self.process:
      self.process.terminate()
