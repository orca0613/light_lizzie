from PySide6.QtCore import Signal
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QMainWindow

from boards.marker_board import MarkerBoard


class MarkerBoardWindow(QMainWindow):
  closed_signal = Signal()

  def __init__(self):
    super().__init__()
    self.board = MarkerBoard(self)
    self.setCentralWidget(self.board)
    self.setWindowTitle("Marker Board")

  def set_last_move(self, x, y):
    self.board.set_last_move(x, y)

  def closeEvent(self, event: QCloseEvent):
    """창이 닫힐 때 PySide6가 자동으로 호출하는 함수"""
    self.closed_signal.emit()  # 컨트롤러에게 신호 발송
    event.accept()  # 창 닫기 승인
