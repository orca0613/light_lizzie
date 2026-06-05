from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QMainWindow

from boards.prediction_board import PredictionBoard
from constants import PREDICTION_BOARD_KEY
from helper import close_window


class PredictionBoardWindow(QMainWindow):
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
    close_window(PREDICTION_BOARD_KEY)
    event.accept()  # 창 닫기 승인
