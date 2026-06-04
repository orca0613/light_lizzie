from PySide6.QtCore import QRectF, Qt, Signal

from boards.base_board import BaseGoBoard


class MainBoard(BaseGoBoard):
  clicked_pos = Signal(int, int)

  def __init__(self, parent=None):
    super().__init__(parent)
    self.transparent_mode = False  # 나무판 배경 필수
    self.stones = {}

  def set_stones(self, stones):
    self.stones = stones
    self.update()

  def mousePressEvent(self, event):
    # 클릭한 위치를 바둑판 좌표로 변환
    x = round((event.position().x() - self.margin) / self.cell_size)
    y = round((event.position().y() - self.margin) / self.cell_size)
    if not (0 <= y < 19 and 0 <= x < 19):
      return
    self.clicked_pos.emit(x, y)

  def draw_overlay_info(self, painter):
    margin = float(self.margin)
    cell_size = self.cell_size

    for loc, color in self.stones.items():
      if color == "K":
        continue
      row, col = divmod(loc, 19)
      cx = margin + col * cell_size
      cy = margin + row * cell_size

      radius = cell_size * 0.45
      stone_rect = QRectF(cx - radius, cy - radius, radius * 2, radius * 2)
      painter.setBrush(Qt.GlobalColor.black if color == "B" else Qt.GlobalColor.white)
      painter.drawEllipse(stone_rect)
