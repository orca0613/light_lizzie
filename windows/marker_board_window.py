from PySide6.QtGui import QCloseEvent, Qt
from PySide6.QtWidgets import QMainWindow

from boards.marker_board import MarkerBoard
from constants import MARKER_BOARD_KEY
from helper import close_window


class MarkerBoardWindow(QMainWindow):
  def __init__(self):
    super().__init__()
    self.board = MarkerBoard(self)
    self.setCentralWidget(self.board)
    self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
    # self.setWindowTitle("Marker Board")

  def set_last_move(self, x, y):
    self.board.set_last_move(x, y)

  def closeEvent(self, event: QCloseEvent):
    close_window(MARKER_BOARD_KEY)
    event.accept()  # 창 닫기 승인
