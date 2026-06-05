from PySide6.QtCore import Signal
from PySide6.QtWidgets import QDialog, QHBoxLayout, QPushButton, QVBoxLayout

from constants import (
  BLACK_ANALYSIS_WINDOW_KEY,
  MARKER_BOARD_KEY,
  OPENING_DATA_BOARD_KEY,
  PREDICTION_BOARD_KEY,
  SHOW_OPTIONS,
  WHITE_ANALYSIS_WINDOW_KEY,
  WINDOW_OPTIONS_JSON_PATH,
  WINRATE_BAR_KEY,
  WINRATE_CHART_KEY,
)
from helper import load_json, update_json
from small_widgets.radio_group_widget import RadioGroupWidget


class WindowSettingDialog(QDialog):
  def __init__(self, parent=None):
    super().__init__(parent)
    self.setWindowTitle("Katago Setting")
    self.setMinimumSize(200, 200)
    self.option_json = load_json(WINDOW_OPTIONS_JSON_PATH)
    self.changed = False

    self.winrate_bar_idx = 0
    self.winrate_chart_idx = 0
    self.marker_board_idx = 0
    self.opening_data_board_idx = 0
    self.prediction_board_idx = 0
    self.black_analysis_window_idx = 0
    self.white_analysis_window_idx = 0

    self.update_option()

    # 메인 레이아웃 (Vertical)
    layout = QVBoxLayout(self)

    self.winrate_bar_group = RadioGroupWidget(
      200,
      "승률 그래프",
      SHOW_OPTIONS,
      self.winrate_bar_idx,
      lambda idx: self._change_option(bool(idx), WINRATE_BAR_KEY),
      self,
    )
    self.winrate_chart_group = RadioGroupWidget(
      200,
      "승률 차트",
      SHOW_OPTIONS,
      self.winrate_chart_idx,
      lambda idx: self._change_option(bool(idx), WINRATE_CHART_KEY),
      self,
    )
    self.marker_board_group = RadioGroupWidget(
      200,
      "마커 보드",
      SHOW_OPTIONS,
      self.marker_board_idx,
      lambda idx: self._change_option(bool(idx), MARKER_BOARD_KEY),
      self,
    )
    self.opening_data_board_group = RadioGroupWidget(
      200,
      "포석 분포",
      SHOW_OPTIONS,
      self.opening_data_board_idx,
      lambda idx: self._change_option(bool(idx), OPENING_DATA_BOARD_KEY),
      self,
    )
    self.prediction_board_group = RadioGroupWidget(
      200,
      "착수 예측",
      SHOW_OPTIONS,
      self.prediction_board_idx,
      lambda idx: self._change_option(bool(idx), PREDICTION_BOARD_KEY),
      self,
    )
    self.black_analysis_window_group = RadioGroupWidget(
      200,
      "흑 분석창",
      SHOW_OPTIONS,
      self.black_analysis_window_idx,
      lambda idx: self._change_option(bool(idx), BLACK_ANALYSIS_WINDOW_KEY),
      self,
    )
    self.white_analysis_window_group = RadioGroupWidget(
      200,
      "백 분석창",
      SHOW_OPTIONS,
      self.white_analysis_window_idx,
      lambda idx: self._change_option(bool(idx), WHITE_ANALYSIS_WINDOW_KEY),
      self,
    )

    layout.addWidget(self.winrate_bar_group)
    layout.addWidget(self.winrate_chart_group)
    layout.addWidget(self.marker_board_group)
    layout.addWidget(self.opening_data_board_group)
    layout.addWidget(self.prediction_board_group)
    layout.addWidget(self.black_analysis_window_group)
    layout.addWidget(self.white_analysis_window_group)

    # 확인 버튼 (Action Buttons) ---
    btn_layout = QHBoxLayout()
    self.cnf_btn = QPushButton("확인")
    btn_layout.addWidget(self.cnf_btn)

    layout.addLayout(btn_layout)

    # 시그널 연결 (Event Handling)
    self.cnf_btn.clicked.connect(self._confirm)  # 창 닫으면서 'OK' 반환

  update_window_setting_signal = Signal()

  def update_option(self):
    option_json = load_json(WINDOW_OPTIONS_JSON_PATH)
    self.winrate_bar_idx = 1 if option_json[WINRATE_BAR_KEY] else 0
    self.winrate_chart_idx = 1 if option_json[WINRATE_CHART_KEY] else 0
    self.marker_board_idx = 1 if option_json[MARKER_BOARD_KEY] else 0
    self.opening_data_board_idx = 1 if option_json[OPENING_DATA_BOARD_KEY] else 0
    self.prediction_board_idx = 1 if option_json[PREDICTION_BOARD_KEY] else 0
    self.black_analysis_window_idx = 1 if option_json[BLACK_ANALYSIS_WINDOW_KEY] else 0
    self.white_analysis_window_idx = 1 if option_json[WHITE_ANALYSIS_WINDOW_KEY] else 0

  def _change_option(self, val: bool, key: str):
    self.changed = True
    self.option_json[key] = val

  def _confirm(self):
    if self.changed:
      update_json(WINDOW_OPTIONS_JSON_PATH, self.option_json)
      self.update_window_setting_signal.emit()
    self.accept()
