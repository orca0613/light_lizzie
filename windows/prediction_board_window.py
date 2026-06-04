from PySide6.QtCore import Signal
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QMainWindow

from boards.prediction_board import PredictionBoard


class PredictionBoardWindow(QMainWindow):
  closed_signal = Signal()

  def __init__(self):
    super().__init__()
    self.board = PredictionBoard(self)
    self.setWindowTitle("Prediction Board")
    self.setCentralWidget(self.board)

  def initialize(self):
    self.board.initialize()

  def set_prediction_list(self, prediction_list):
    self.board.set_prediction_list(prediction_list)

  def closeEvent(self, event: QCloseEvent):
    """창이 닫힐 때 PySide6가 자동으로 호출하는 함수"""
    self.closed_signal.emit()  # 컨트롤러에게 신호 발송
    event.accept()  # 창 닫기 승인
