import sys
import time
from typing import Dict
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QTimer
from api import get_player_data
from constants import BLACK_ANALYSIS_WINDOW_KEY, DISPLAY_SETTING_JSON_PATH, KATAGO_SETTING_JSON_PATH, KATAGO_VAR_PATH, KOMI_KEY, MARKER_BOARD_KEY, MAX_ANALYSIS_TIME_KEY, MAX_VISIT_KEY, OPENING_BOARD_KEY, RULE_KEY, UPDATE_CYCLE_KEY, WHITE_ANALYSIS_WINDOW_KEY, WINDOW_OPTIONS_JSON_PATH, WINRATE_BAR_KEY, WINRATE_CHART_KEY
from engine import KataGoGTP
from helper import close_window, get_best_from_katago_response, get_past_num_date, load_json, to_gtp_coord, update_json
from windows.analysis import AnalysisWindow
from windows.main_board import MainBoard
from windows.marker_board import MarkerBoard
from windows.opening_data_board import OpeningDataBoard
from windows.winrate_bar import WinrateBar
from windows.winrate_chart import WinrateChartWindow

class MainController:
  def __init__(self):
    self.display_setting_json = load_json(DISPLAY_SETTING_JSON_PATH)
    self.katago_setting_json = load_json(KATAGO_SETTING_JSON_PATH)

    # 윈도우 창 설정
    
    self.main_board = MainBoard()
    self.marker_board = MarkerBoard()
    self.opening_data_board = OpeningDataBoard()

    self.winrate_bar = WinrateBar()
    self.winrate_chart = WinrateChartWindow()

    self.black_analysis_window = AnalysisWindow("black")
    self.white_analysis_window = AnalysisWindow("white")

    self.sub_windows = [
      self.winrate_bar, 
      self.winrate_chart,
      self.marker_board, 
      self.opening_data_board,
      self.black_analysis_window, 
      self.white_analysis_window
    ]

    # 각 윈도우의 시그널 연결

    self.main_board.undo_signal.connect(self._undo)
    self.main_board.clicked_pos.connect(self._play_move)
    self.main_board.update_katago_path_signal.connect(self._check_katago_path)
    self.main_board.update_katago_setting_signal.connect(self._update_katago_setting)
    self.main_board.update_display_setting_signal.connect(self._update_display_setting)
    self.main_board.update_player_name_signal.connect(self._update_player)
    self.main_board.update_window_setting_signal.connect(self._update_window_setting)
    self.main_board.update_position_signal.connect(self._update_position)
    self.main_board.closed_signal.connect(self._close_windows)

    # 엔진 및 카타고 분석 변수 설정

    self.engine = None
    self._set_engine()
    self.engine_running = False
    self.analysis_time = float("inf")

    self.moves = []

    # 엔진 초기화

    if self.engine:
      self.engine.clear_board()
      self.engine.set_rule_and_komi(self.katago_setting_json[RULE_KEY], self.katago_setting_json[KOMI_KEY])
      self._start_analyze()

    
    # 분석 업데이트 타이머
    update_cycle = self.katago_setting_json[UPDATE_CYCLE_KEY]
    self.analysis_timer = QTimer()
    self.analysis_timer.timeout.connect(self.process_latest_analysis)
    self.analysis_timer.start(update_cycle)

  
  def _set_engine(self):
    katago_var_json = load_json(KATAGO_VAR_PATH)
    katago = katago_var_json["exe"]
    model = katago_var_json["model"]
    config = katago_var_json["config"]

    if not katago:
      return QMessageBox.warning(self.main_board, "카타고 경로 오류", "카타고 실행 파일 경로를 설정해 주세요!")
    if not model:
      return QMessageBox.warning(self.main_board, "가중치 파일 경로 오류", "가중치 파일 경로를 설정해 주세요!")
    if not config:
      return QMessageBox.warning(self.main_board, "컨피그 파일 경로 오류", "컨피그 파일 경로를 설정해 주세요!")
    
    self.engine = KataGoGTP(katago, model, config)
    print("엔진이 준비 되었습니다.")


  def _play_move(self, y: int, x: int):
    self.moves.append((y, x))
    self.marker_board.set_last_move(y, x)

    if not self.engine:
      QMessageBox.warning(self.main_board, "에러", "엔진 설정이 필요합니다.")
      return
    
    # [수정] 흑/백 결정 로직 (자체 UI 업데이트)
    # 0.5초 타이머가 이전 분석 결과를 그리지 않도록 미리 비워줌
    self.engine.last_analysis = "" 
    
    color_str = "white" if self.main_board.move_number % 2 == 0 else "black"
    
    vertex = to_gtp_coord(x, y)
    
    # 1. 엔진에 한 수 전달 (비동기)
    self.engine.play_move(color_str, vertex)
    self.winrate_chart.play_move()
    
    # 2. 엔진에 분석 시작 요청
    self._start_analyze()


  def process_latest_analysis(self):
    """0.5초마다 호출되어 엔진의 최신 분석 결과(last_analysis)를 처리"""
    if not self.engine or not self.engine.last_analysis or not self.engine_running:
      return
    
    is_white_turn = bool(self.main_board.move_number % 2)
    max_analysis_time = self.katago_setting_json[MAX_ANALYSIS_TIME_KEY]
    max_visit = self.katago_setting_json[MAX_VISIT_KEY]
    line = self.engine.last_analysis
    # analysis_array = parse_full_katago_string(line)
    best_data = get_best_from_katago_response(line)
    # if (analysis_array):
    #   best_data = analysis_array[0]
    winrate = round(best_data["winrate"] * 10) / 10
    score = round(best_data["scoreLead"] * 10) / 10
    complexity = round(best_data["scoreStdev"] * 10) / 10
    visits = best_data["visits"]
    cur_time = time.time()
    if (cur_time - self.analysis_time > max_analysis_time) or visits > max_visit:
      self._stop_analyze()
      return
    if is_white_turn:
      winrate = 100 - winrate
      score = -score
    self.winrate_bar.update_data(winrate, score)
    self.winrate_chart.update_winrate(winrate)
    if is_white_turn:
      self.white_analysis_window.update_analysis_data(self.main_board.move_number, winrate, score, complexity)
    else:
      self.black_analysis_window.update_analysis_data(self.main_board.move_number, winrate, score, complexity)


  def _undo(self):
    self.moves.pop()
    if not self.moves:
      self.marker_board.set_last_move(-1, -1)
    else:
      y, x = self.moves[-1]
      self.marker_board.set_last_move(y, x)
    self.winrate_chart.undo()
    self.engine.undo()
    self._start_analyze()


  def _check_katago_path(self):
    katago_var_json = load_json(KATAGO_VAR_PATH)
    katago = katago_var_json["exe"]
    model = katago_var_json["model"]
    config = katago_var_json["config"]

    if not katago:
      return QMessageBox.warning(self.main_board, "카타고 경로 오류", "카타고 실행 파일 경로를 설정해 주세요!")
    if not model:
      return QMessageBox.warning(self.main_board, "가중치 파일 경로 오류", "가중치 파일 경로를 설정해 주세요!")
    if not config:
      return QMessageBox.warning(self.main_board, "컨피그 파일 경로 오류", "컨피그 파일 경로를 설정해 주세요!")
    
    QMessageBox.information(self.main_board, "", "변경 사항은 재부팅 후 반영됩니다.")


  def _update_katago_setting(self):
    katago_setting_json = load_json(KATAGO_SETTING_JSON_PATH)
    self.katago_setting_json = katago_setting_json
    rule = katago_setting_json[RULE_KEY]
    komi = katago_setting_json[KOMI_KEY]
    update_cycle = katago_setting_json[UPDATE_CYCLE_KEY]
    self.analysis_timer.start(update_cycle)
    self.engine.set_rule_and_komi(rule, komi)
    self._start_analyze()


  def _start_analyze(self):
    self.engine.start_analyze()
    self.engine_running = True
    self.analysis_time = time.time()
  

  def _stop_analyze(self):
    self.engine.stop_analyze()
    self.engine_running = False


  def _update_display_setting(self):
    self.main_board.update_board_display()
    self.marker_board.update_board_display()
    self.opening_data_board.update_board_display()
    self.winrate_bar.update_bar_display()


  def _update_player(self, black: str, white: str):
    black_player = get_player_data(black)
    white_player = get_player_data(white)
    if black_player:
      black_code = black_player["playerCode"]
      self.black_analysis_window.update_player(black, black_code)
      self.opening_data_board.update_black_data(black_code)
    else:
      QMessageBox.warning(self.main_board, "경고", "흑 플레이어를 찾을 수 없습니다.")
      self.black_analysis_window.update_player("", 0)
    if white_player:
      white_code = white_player["playerCode"]
      self.white_analysis_window.update_player(white, white_code)
      self.opening_data_board.update_white_data(white_code)
    else:
      QMessageBox.warning(self.main_board, "경고", "백 플레이어를 찾을 수 없습니다.")
      self.white_analysis_window.update_player("", 0)


  def _update_window_setting(self):
    sub_window_keys = [
      WINRATE_BAR_KEY, 
      WINRATE_CHART_KEY, 
      MARKER_BOARD_KEY,
      OPENING_BOARD_KEY,
      BLACK_ANALYSIS_WINDOW_KEY, 
      WHITE_ANALYSIS_WINDOW_KEY
    ]
    window_options_json = load_json(WINDOW_OPTIONS_JSON_PATH)
    for i, key in enumerate(sub_window_keys):
      if window_options_json[key]:
        self.sub_windows[i].show()
      else:
        self.sub_windows[i].close()

  
  def _update_analysis_data(self, analysis_data: Dict, is_white_turn: bool):
    count = analysis_data["totalCount"]
    delta_winrate = analysis_data["deltaWinrate"]
    delta_score = analysis_data["deltaScore"]
    bluespot_ratio = analysis_data["blueSpotRatio"] * 100
    if is_white_turn:
      self.white_analysis_window.update_data(delta_winrate, delta_score, bluespot_ratio, count)
    else:
      self.black_analysis_window.update_data(delta_winrate, delta_score, bluespot_ratio, count)

  
  def _update_position(self, ps: str):
    self.opening_data_board.update_position(ps, self.main_board.move_number)


  def _close_windows(self):
    close_window("all")
    self.opening_data_board.close()
    for window in self.sub_windows:
      window.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 컨트롤러 생성 및 실행
    controller = MainController()
    controller.main_board.show()
    
    sys.exit(app.exec())