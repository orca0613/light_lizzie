import pandas as pd
from PySide6.QtGui import QCloseEvent, Qt
from PySide6.QtWidgets import QMainWindow

from api import get_move_data
from boards.opening_data_board import OpeningDataBoard
from constants import BOARD_SIZE_KEY, DISPLAY_SETTING_JSON_PATH, OPENING_DATA_BOARD_KEY
from helper import close_window, get_past_num_date, load_json


class OpeningDataBoardWindow(QMainWindow):
  def __init__(self):
    super().__init__()
    self.board = OpeningDataBoard(self)
    self.setCentralWidget(self.board)
    self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

    self.black_code = 0
    self.white_code = 0
    self.black_data = None
    self.white_data = None
    self.gt = 2
    self.ref_date = get_past_num_date(5, 0)
    self.ps = "0"
    self.move_number = 0

  def mousePressEvent(self, event):
    # 마우스 클릭 시 창의 원래 위치와 마우스 커서 위치의 차이(오프셋)를 저장
    if event.button() == Qt.MouseButton.LeftButton:
      self.drag_position = (
        event.globalPosition().toPoint() - self.frameGeometry().topLeft()
      )
      event.accept()

  def mouseMoveEvent(self, event):
    # 마우스를 누른 채 움직이면 창을 같이 이동시킴
    if event.buttons() == Qt.MouseButton.LeftButton:
      self.move(event.globalPosition().toPoint() - self.drag_position)
      event.accept()

  def update_black_data(self, player_code):
    if player_code == self.black_code:
      return
    opening_move_data = get_move_data(player_code)
    self.black_data = pd.DataFrame(opening_move_data)
    self.update_position(self.ps, self.move_number)

  def update_white_data(self, player_code):
    if player_code == self.white_code:
      return
    opening_move_data = get_move_data(player_code)
    self.white_data = pd.DataFrame(opening_move_data)
    self.update_position(self.ps, self.move_number)

  def update_position(self, ps: str, move_number: int):
    self.ps = ps
    self.move_number = move_number
    if move_number % 2:
      if self.white_data is None:
        return
      mv_series = self.white_data.loc[
        (self.white_data["dt"] >= self.ref_date) & (self.white_data["ps"] == ps), "mv"
      ]
      self._update_opening_data(mv_series)
    else:
      if self.black_data is None:
        return
      mv_series = self.black_data.loc[
        (self.black_data["dt"] >= self.ref_date) & (self.black_data["ps"] == ps), "mv"
      ]
      self._update_opening_data(mv_series)
    # self.update() # 화면을 다시 그리도록 요청 (paintEvent 트리거)

  def _update_opening_data(self, series):
    total_count = len(series)
    counter = series.value_counts()
    opening_data = []
    for key, value in counter.items():
      opening_data.append((key, value, (value / total_count) * 100))
    self.board.set_opening_data(opening_data)

  def update_board_display(self):
    setting_json = load_json(DISPLAY_SETTING_JSON_PATH)
    self.board_size = setting_json[BOARD_SIZE_KEY]
    self.margin = self.board_size / 20
    self.resize(self.board_size, self.board_size)

  def closeEvent(self, event: QCloseEvent):
    close_window(OPENING_DATA_BOARD_KEY)
    event.accept()
