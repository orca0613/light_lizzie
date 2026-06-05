from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont

from boards.base_board import BaseGoBoard


def get_color_by_frequency(freq: float):
  alpha = 128
  if freq >= 50:
    return QColor(99, 204, 255, alpha)
  if freq >= 40:
    return QColor(174, 198, 207, alpha)
  if freq >= 30:
    return QColor(173, 216, 230, alpha)
  if freq >= 20:
    return QColor(188, 238, 188, alpha)
  if freq >= 10:
    return QColor(255, 255, 181, alpha)
  return QColor(255, 210, 168, alpha)


class OpeningDataBoard(BaseGoBoard):
  def __init__(self, parent=None):
    super().__init__(parent)
    self.transparent_mode = True
    self.opening_data = []

  def initialize(self):
    self.opening_data = []
    self.update()

  def set_opening_data(self, opening_data):
    self.opening_data = opening_data
    self.update()

  def draw_overlay_info(self, painter):
    for loc, cnt, freq in self.opening_data:
      x, y = loc % 19, loc // 19
      # 실제 그릴 중심점 픽셀 좌표 계산
      center_x = self.margin + x * self.cell_size
      center_y = self.margin + y * self.cell_size
      circle_color = get_color_by_frequency(freq)

      radius = self.cell_size * 0.45
      move_rect = QRectF(center_x - radius, center_y - radius, radius * 2, radius * 2)

      painter.setBrush(circle_color)
      painter.setPen(circle_color)
      painter.drawEllipse(move_rect)

      # 1. 표시할 각각의 변수 설정
      cnt_text = str(cnt)  # 첫 번째 줄에 들어갈 변수
      freq_text = str(round(freq, 1)) + "%"  # 두 번째 줄에 들어갈 변수

      # 2. 폰트 설정 (두 줄이 들어가므로 크기를 기존보다 조금 줄이는 것이 좋습니다)
      cnt_font = QFont("Arial", int(self.cell_size * 0.3))
      painter.setFont(cnt_font)
      painter.setPen(Qt.GlobalColor.black)

      # 3. 영역 쪼개기 (기존 사각형의 높이를 절반으로 나누기)
      half_height = move_rect.height() / 2

      # 상단 줄 영역 (기존 사각형의 상단 절반)
      top_rect = QRectF(
        move_rect.left(), move_rect.top(), move_rect.width(), half_height
      )

      # 하단 줄 영역 (기존 사각형의 하단 절반)
      bottom_rect = QRectF(
        move_rect.left(), move_rect.top() + half_height, move_rect.width(), half_height
      )

      # 4. 각각의 영역에 변수 출력 (정중앙 정렬)
      painter.drawText(top_rect, Qt.AlignmentFlag.AlignCenter, cnt_text)

      # 2. 폰트 설정 (두 줄이 들어가므로 크기를 기존보다 조금 줄이는 것이 좋습니다)
      freq_font = QFont("Arial", int(self.cell_size * 0.2))
      painter.setFont(freq_font)
      painter.setPen(Qt.GlobalColor.black)

      painter.drawText(bottom_rect, Qt.AlignmentFlag.AlignCenter, freq_text)
