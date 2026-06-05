from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont

from boards.base_board import BaseGoBoard


def get_color_by_similarity(similarity: float):
  alpha = 128
  if similarity >= 50:
    return QColor(99, 204, 255, alpha)
  if similarity >= 40:
    return QColor(174, 198, 207, alpha)
  if similarity >= 30:
    return QColor(173, 216, 230, alpha)
  if similarity >= 20:
    return QColor(188, 238, 188, alpha)
  if similarity >= 10:
    return QColor(255, 255, 181, alpha)
  return QColor(255, 210, 168, alpha)


class PredictionBoard(BaseGoBoard):
  def __init__(self, parent=None):
    super().__init__(parent)
    self.transparent_mode = False  # 나무판 배경 필수
    self.prediction_list = []

  def initialize(self):
    self.prediction_list = []
    self.update()

  def set_prediction_list(self, prediction_list):
    self.prediction_list = prediction_list
    self.update()

  def draw_overlay_info(self, painter):
    for similarity, loc in self.prediction_list:
      x, y = loc % 19, loc // 19
      # 실제 그릴 중심점 픽셀 좌표 계산
      center_x = self.margin + x * self.cell_size
      center_y = self.margin + y * self.cell_size
      circle_color = get_color_by_similarity(similarity * 100)

      radius = self.cell_size * 0.45
      move_rect = QRectF(center_x - radius, center_y - radius, radius * 2, radius * 2)

      # 1. 커스텀 컬러 및 투명도 설정 (Red, Green, Blue, Alpha)
      # Alpha 값은 0(완전 투명) ~ 255(완전 불투명) 사이로 조절합니다.

      painter.setBrush(circle_color)

      # 원 테두리 색상 설정 (원하는 경우 테두리는 투명하게 없앨 수도 있습니다: Qt.PenStyle.NoPen)
      painter.setPen(circle_color)

      painter.drawEllipse(move_rect)

      similarity_text = (
        str(round(similarity * 100, 1)) + "%"
      )  # 두 번째 줄에 들어갈 변수

      # 2. 폰트 설정
      font = QFont("Arial", int(self.cell_size * 0.3))
      painter.setFont(font)
      painter.setPen(Qt.GlobalColor.black)

      painter.drawText(move_rect, Qt.AlignmentFlag.AlignCenter, similarity_text)
