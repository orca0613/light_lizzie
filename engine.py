import os
import queue
import subprocess
import sys
import threading
import time
import traceback
from pathlib import Path

from constants import ANALYZE_COMMAND, KOMI_KEY, RULE_KEY

_LOG_PATH = Path.home() / "light_lizzie_engine_debug.log"
_log_file = open(_LOG_PATH, "a", encoding="utf-8", buffering=1)  # line-buffered
_log_lock = threading.Lock()


def _log(msg):
  ts = time.strftime("%H:%M:%S") + f".{int((time.time() % 1) * 1000):03d}"
  tname = threading.current_thread().name
  with _log_lock:
    print(f"{ts} [{tname}] {msg}", file=_log_file, flush=True)


_log("=" * 60)
_log(
  f"KataGoGTP debug log start pid={os.getpid()} platform={sys.platform} py={sys.version.split()[0]}"
)
_log(f"log file: {_LOG_PATH}")


class KataGoGTP:
  def __init__(self, exe_path, model_path, config_path):
    # 1. 프로세스 실행
    cmd = [exe_path, "gtp", "-model", model_path, "-config", config_path]
    _log(f"launching: {cmd}")
    self.process = subprocess.Popen(
      cmd,
      stdin=subprocess.PIPE,
      stdout=subprocess.PIPE,
      stderr=subprocess.PIPE,
      text=True,
      encoding="utf-8",
      errors="replace",
      bufsize=1,
    )
    _log(f"subprocess pid={self.process.pid}")

    self.last_analysis = ""  # 최신 분석 텍스트 저장
    self.is_running = True
    self.analysis_callback = None  # UI 업데이트용 콜백 (선택 사항)
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
      _log(f"engine exited early: {error_msg}")
      print(f"엔진 조기 종료 에러:\n{error_msg}")
      return

    # 3. [핵심] 모든 출력을 읽어들일 단 하나의 리스너 스레드 시작
    self.listener_thread = threading.Thread(
      target=self._listen, name="kata-stdout", daemon=True
    )
    self.listener_thread.start()
    self.stderr_thread = threading.Thread(
      target=self._drain_stderr, name="kata-stderr", daemon=True
    )
    self.stderr_thread.start()
    self.watchdog_thread = threading.Thread(
      target=self._watchdog, name="kata-watchdog", daemon=True
    )
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
          _log(f"stderr EOF (engine returncode={self.process.poll()})")
          break
        _log(f"STDERR: {line.rstrip()}")
    except Exception:
      _log(f"_drain_stderr crashed:\n{traceback.format_exc()}")

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
        _log(
          f"WATCHDOG stuck {stuck_for:.1f}s: sent={self.sent_cmd_id} acked={self.acked_cmd_id} "
          f"queue={self.cmd_queue.qsize()} listener_alive={self.listener_thread.is_alive()} "
          f"stderr_alive={self.stderr_thread.is_alive()} engine_alive={self.process.poll() is None}"
        )
        last_warn_at = time.time()

  def _listen(self):
    """엔진의 stdout을 독점적으로 모니터링하는 스레드 함수"""
    try:
      while self.is_running and self.process.poll() is None:
        line = self.process.stdout.readline()
        if not line:
          _log(f"stdout EOF (engine returncode={self.process.poll()})")
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
            _log(f"STDOUT info heartbeat: {self._info_count} info lines total")
            self._last_info_log = now
          if self.analysis_callback:
            # 주의: 이 콜백은 리스너 스레드에서 실행됨
            try:
              self.analysis_callback(line)
            except Exception:
              _log(f"analysis_callback raised:\n{traceback.format_exc()}")

        # 일반 응답(=) 처리 (필요 시 로그 출력)
        elif line.startswith("="):
          _log(f"STDOUT response: {line[:200]!r}")
          rest = line[1:].strip()
          if not rest:
            _log(f"response had no id payload: {line!r} — pre-fix this killed listener")
            continue
          first_tok = rest.split()[0]
          try:
            cmd_id = int(first_tok)
          except ValueError:
            _log(
              f"could not parse cmd id from {line!r} (first token {first_tok!r}) — pre-fix this killed listener"
            )
            continue
          _log(
            f"ACK id={cmd_id} (sent={self.sent_cmd_id} acked_before={self.acked_cmd_id} queue={self.cmd_queue.qsize()})"
          )
          self.acked_cmd_id = cmd_id + 1
          self.is_waiting = False
          self._wait_started_at = None
          self._process_request()
        else:
          _log(f"STDOUT other: {line[:200]}")
    except Exception:
      _log(
        f"_listen crashed (would silently freeze the app):\n{traceback.format_exc()}"
      )

  def send_command(self, command):
    _log(
      f"send_command({command!r}) sent={self.sent_cmd_id} acked={self.acked_cmd_id} "
      f"waiting={self.is_waiting} queue={self.cmd_queue.qsize()}"
    )
    self.cmd_queue.put((self.sent_cmd_id, command))
    self.sent_cmd_id += 1
    self._process_request()

  def _process_request(self):
    caller = threading.current_thread().name
    if self.is_waiting or self.acked_cmd_id == self.sent_cmd_id:
      _log(
        f"_process_request skip caller={caller} waiting={self.is_waiting} "
        f"sent={self.sent_cmd_id} acked={self.acked_cmd_id}"
      )
      return
    try:
      id, command = self.cmd_queue.get_nowait()
    except queue.Empty:
      _log(
        f"_process_request: queue empty though sent != acked caller={caller} "
        f"sent={self.sent_cmd_id} acked={self.acked_cmd_id}"
      )
      return
    _log(f"STDIN  -> id={id} {command}  (caller={caller})")
    try:
      self.process.stdin.write(f"{id} {command}\n")
      self.process.stdin.flush()
    except Exception:
      _log(f"stdin write failed for {command!r}:\n{traceback.format_exc()}")
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
    _log("close() called")
    self.is_running = False
    if self.process:
      self.process.terminate()
