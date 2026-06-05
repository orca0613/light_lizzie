from PySide6.QtCore import QRectF, Qt

from boards.base_board import BaseGoBoard


class MarkerBoard(BaseGoBoard):
  def __init__(self, parent=None):
    super().__init__(parent)
    self.transparent_mode = False
    self.last_move = None

  def set_last_move(self, x, y):
    if x < 0 or y < 0:
      self.last_move = None
    else:
      self.last_move = (x, y)
    self.update()

  def draw_overlay_info(self, painter):
    if self.last_move is None:
      return

    x, y = self.last_move

    # 실제 그릴 중심점 픽셀 좌표 계산
    center_x = self.margin + x * self.cell_size
    center_y = self.margin + y * self.cell_size

    radius = self.cell_size * 0.2
    move_rect = QRectF(center_x - radius, center_y - radius, radius * 2, radius * 2)

    painter.setBrush(Qt.GlobalColor.red)
    painter.setPen(Qt.GlobalColor.red)
    painter.drawEllipse(move_rect)
