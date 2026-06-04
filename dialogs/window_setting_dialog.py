from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton)
from PySide6.QtCore import Signal

from constants import BLACK_ANALYSIS_WINDOW_KEY, MARKER_BOARD_KEY, OPENING_BOARD_KEY, SHOW_OPTIONS, WHITE_ANALYSIS_WINDOW_KEY, WINDOW_OPTIONS_JSON_PATH, WINRATE_BAR_KEY, WINRATE_CHART_KEY
from helper import load_json, update_json
from small_widgets.radio_group_widget import RadioGroupWidget

class WindowSettingDialog(QDialog):
  def __init__(self, parent=None):
    super().__init__(parent)
    self.setWindowTitle("Katago Setting")
    self.setMinimumSize(200, 200)
    self.option_json = load_json(WINDOW_OPTIONS_JSON_PATH)
    self.changed = False
    
    # 메인 레이아웃 (Vertical)
    layout = QVBoxLayout(self)
    winrate_bar_idx = 1 if self.option_json[WINRATE_BAR_KEY] else 0
    winrate_chart_idx = 1 if self.option_json[WINRATE_CHART_KEY] else 0
    marker_board_idx = 1 if self.option_json[MARKER_BOARD_KEY] else 0
    opening_board_idx = 1 if self.option_json[OPENING_BOARD_KEY] else 0
    black_analysis_window_idx = 1 if self.option_json[BLACK_ANALYSIS_WINDOW_KEY] else 0
    white_analysis_window_idx = 1 if self.option_json[WHITE_ANALYSIS_WINDOW_KEY] else 0

    self.winrate_bar_group = RadioGroupWidget(200, "승률 그래프", SHOW_OPTIONS, winrate_bar_idx, self._update_winrate_bar_option, self)
    self.winrate_chart_group = RadioGroupWidget(200, "승률 차트", SHOW_OPTIONS, winrate_chart_idx, self._update_winrate_chart_option, self)
    self.marker_board_group = RadioGroupWidget(200, "마커 보드", SHOW_OPTIONS, marker_board_idx, self._update_marker_board_option, self)
    self.opening_board_group = RadioGroupWidget(200, "포석 분포", SHOW_OPTIONS, opening_board_idx, self._update_opening_board_option, self)
    self.black_analysis_window_group = RadioGroupWidget(200, "흑 분석창", SHOW_OPTIONS, black_analysis_window_idx, self._update_black_analysis_window_option, self)
    self.white_analysis_window_group = RadioGroupWidget(200, "백 분석창", SHOW_OPTIONS, white_analysis_window_idx, self._update_white_analysis_window_option, self)


    layout.addWidget(self.winrate_bar_group)
    layout.addWidget(self.winrate_chart_group)
    layout.addWidget(self.marker_board_group)
    layout.addWidget(self.opening_board_group)
    layout.addWidget(self.black_analysis_window_group)
    layout.addWidget(self.white_analysis_window_group)
    
    # 확인 버튼 (Action Buttons) ---
    btn_layout = QHBoxLayout()
    self.cnf_btn = QPushButton("확인")
    btn_layout.addWidget(self.cnf_btn)

    layout.addLayout(btn_layout)

    # 시그널 연결 (Event Handling)
    self.cnf_btn.clicked.connect(self._confirm) # 창 닫으면서 'OK' 반환
  
  update_window_setting_signal = Signal()

  def _update_winrate_bar_option(self, idx: int):
    self.changed = True
    self.option_json[WINRATE_BAR_KEY] = bool(idx)
    return
  

  def _update_winrate_chart_option(self, idx: int):
    self.changed = True
    self.option_json[WINRATE_CHART_KEY] = bool(idx)
    return
  
  
  def _update_marker_board_option(self, idx: int):
    self.changed = True
    self.option_json[MARKER_BOARD_KEY] = bool(idx)
    return
  

  def _update_opening_board_option(self, idx: int):
    self.changed = True
    self.option_json[OPENING_BOARD_KEY] = bool(idx)
    return
  

  def _update_black_analysis_window_option(self, idx: int):
    self.changed = True
    self.option_json[BLACK_ANALYSIS_WINDOW_KEY] = bool(idx)
    return


  def _update_white_analysis_window_option(self, idx: int):
    self.changed = True
    self.option_json[WHITE_ANALYSIS_WINDOW_KEY] = bool(idx)
    return


  def _confirm(self):
    if self.changed:
      update_json(WINDOW_OPTIONS_JSON_PATH, self.option_json)
      self.update_window_setting_signal.emit()
    self.accept()