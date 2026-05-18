import json
import subprocess
import threading
import time
from typing import Dict

from constants import KOMI_KEY, RULE_KEY

class KataGoGTP:
  def __init__(self, exe_path, model_path, config_path):
    # 1. 프로세스 실행
    cmd = [exe_path, "gtp", "-model", model_path, "-config", config_path]
    self.process = subprocess.Popen(
      cmd,
      stdin=subprocess.PIPE,
      stdout=subprocess.PIPE,
      stderr=subprocess.PIPE,
      text=True,
      encoding='utf-8',
      bufsize=1
    )

    self.last_analysis = ""      # 최신 분석 텍스트 저장
    self.is_running = True
    self.analysis_callback = None # UI 업데이트용 콜백 (선택 사항)

    # 2. 엔진 로딩 확인
    time.sleep(1) 
    if self.process.poll() is not None:
      error_msg = self.process.stderr.read()
      print(f"엔진 조기 종료 에러:\n{error_msg}")
      return

    # 3. [핵심] 모든 출력을 읽어들일 단 하나의 리스너 스레드 시작
    self.listener_thread = threading.Thread(target=self._listen, daemon=True)
    self.listener_thread.start()


  def clear_board(self):
    self.send_command("clear_board")

  
  def set_rule_and_komi(self, rule: str, komi: float):
    self.send_command(f"{RULE_KEY} {rule}")
    self.send_command(f"{KOMI_KEY} {komi}")
      

  def _listen(self):
    """엔진의 stdout을 독점적으로 모니터링하는 스레드 함수"""
    while self.is_running and self.process.poll() is None:
      line = self.process.stdout.readline()
      if not line:
        break
      
      line = line.strip()
      if not line:
        continue

      # 분석 정보(info)인 경우 보관 및 콜백 실행
      if line.startswith("info"):
        self.last_analysis = line
        if self.analysis_callback:
          # 주의: 이 콜백은 리스너 스레드에서 실행됨
          self.analysis_callback(line)
  
      # 일반 응답(=) 처리 (필요 시 로그 출력)
      elif line.startswith("="):
        # print(f"[Engine Output]: {line}")
        pass


  def send_command(self, command):
    """[비동기] 명령어를 보내기만 하고 즉시 복귀 (Non-blocking)"""
    if not self.process or self.process.poll() is not None:
      return
    
    try:
      self.process.stdin.write(command + "\n")
      self.process.stdin.flush()
    except Exception as e:
      print(f"명령어 전송 중 에러: {e}")


  def play_move(self, color, vertex):
    """한 수를 놓음 (B Q16 등)"""
    self.send_command(f"play {color} {vertex}")

  
  def undo(self):
    """한 수 무르기"""
    self.send_command("undo")


  def start_analyze(self, callback=None):
    """분석 시작 (콜백 함수를 등록할 수 있음)"""
    self.analysis_callback = callback
    self.send_command("kata-analyze 10")


  def stop_analyze(self):
    """분석 중단"""
    # GTP에서 아무 명령이나 보내면 분석이 중단됨
    self.send_command("stop")
    self.analysis_callback = None


  def close(self):
    """엔진 종료"""
    self.is_running = False
    if self.process:
      self.process.terminate()