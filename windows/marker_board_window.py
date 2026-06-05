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

  def set_last_move(self, x, y):
    self.board.set_last_move(x, y)

  def closeEvent(self, event: QCloseEvent):
    close_window(MARKER_BOARD_KEY)
    event.accept()  # 창 닫기 승인
