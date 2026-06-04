from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QCloseEvent, QColor, QFont, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import QMainWindow

from constants import (
  DISPLAY_SETTING_JSON_PATH,
  IS_WHITE_FIRST_KEY,
  WINRATE_BAR_HEIGHT_KEY,
  WINRATE_BAR_KEY,
  WINRATE_BAR_WIDTH_KEY,
)
from helper import close_window, load_json

black_primary_color = "#000000"
black_sub_color = "#2c2c2c"
white_primary_color = "#ffffff"
white_sub_color = "#e0e0e0"


class WinrateBar(QMainWindow):
  def __init__(self):
    super().__init__()
    self.setWindowTitle("Winrate Bar")
    # 1. 테두리 없는 창 생성 및 작업 표시줄에서 숨김 (선택)
    # self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
    self.bar_width = 0
    self.bar_height = 0
    self.is_white_first = None
    self.black_winrate = 50.0
    self.black_score = 0
    self.update_bar_display()

  def update_data(self, winrate, score):
    self.black_winrate = winrate
    self.black_score = score
    self.update()

  def paintEvent(self, event):
    painter = QPainter(self)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # --- 레이아웃 계산 ---
    # 2. 바(Bar)가 그려질 높이를 전체 높이의 60% 정도로 제한
    bar_height = self.bar_height * 0.6
    rect = QRectF(1, 1, self.bar_width - 2, bar_height)
    w = rect.width()
    h = rect.height()
    radius = bar_height / 2
    white_winrate = 100 - self.black_winrate

    base_prime_color = (
      black_primary_color if self.is_white_first else white_primary_color
    )
    base_sub_color = black_sub_color if self.is_white_first else white_sub_color
    top_prime_color = (
      white_primary_color if self.is_white_first else black_primary_color
    )
    top_sub_color = white_sub_color if self.is_white_first else black_sub_color

    # 1. 베이스 (sub color)
    painter.setPen(QPen(QColor("#d1d1d1"), 1))
    bg_gradient = QLinearGradient(0, 0, 0, h)
    bg_gradient.setColorAt(0, QColor(base_prime_color))
    bg_gradient.setColorAt(1, QColor(base_sub_color))
    painter.setBrush(bg_gradient)
    painter.drawRoundedRect(rect, radius, radius)

    # 2. 탑 (top color)
    top_winrate = white_winrate if self.is_white_first else self.black_winrate
    top_w = w * (top_winrate / 100.0)
    if top_w > 0:
      top_rect = QRectF(rect.x(), rect.y(), top_w, h)
      top_gradient = QLinearGradient(0, 0, 0, h)
      top_gradient.setColorAt(0, QColor(top_sub_color))
      top_gradient.setColorAt(1, QColor(top_prime_color))
      painter.setBrush(top_gradient)
      painter.setPen(Qt.NoPen)

      painter.save()
      painter.setClipPath(self._get_round_rect_path(rect, radius))
      painter.drawRect(top_rect)
      painter.restore()

    # 3. 중앙 분리선
    painter.setPen(QPen(QColor(128, 128, 128, 120), 1))
    painter.drawLine(w / 2, 0, w / 2, h)

    # --- 텍스트 그리기 영역 ---

    # 4. 바 내부의 점수(pts) 표시 (기존 로직 유지)
    score_font = QFont("Arial", h / 2.5, QFont.Weight.Bold)
    painter.setFont(score_font)
    score_str = f"{abs(self.black_score):.1f} pts"
    top_score = -self.black_score if self.is_white_first else self.black_score
    pen_color = Qt.white if self.black_score >= 0 else Qt.black

    if top_score > 0:
      painter.setPen(pen_color)
      painter.drawText(
        top_rect.adjusted(0, 0, -10, 0), Qt.AlignRight | Qt.AlignVCenter, score_str
      )
    else:
      painter.setPen(pen_color)
      text_rect = QRectF(top_w + 10, 0, w - top_w - 20, h)
      painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, score_str)

    # 5. 바 아래 양쪽 끝 승률(%) 표시 (새로 추가)
    percent_font = QFont("Arial", 10, QFont.Weight.Medium)
    painter.setFont(percent_font)
    painter.setPen(QColor("#363636"))  # 가독성을 위해 진한 회색

    # 텍스트가 그려질 y 좌표 (바 하단에서 약간 띄움)
    text_y = h + 5
    text_h = self.bar_height - text_y

    # 왼쪽 끝
    left_percent_str = (
      f"{white_winrate:.1f}%" if self.is_white_first else f"{self.black_winrate:.1f}%"
    )
    painter.drawText(
      QRectF(0, text_y, w, text_h), Qt.AlignLeft | Qt.AlignTop, left_percent_str
    )

    # 오른쪽 끝
    right_percent_str = (
      f"{self.black_winrate:.1f}%" if self.is_white_first else f"{white_winrate:.1f}%"
    )
    painter.drawText(
      QRectF(0, text_y, w, text_h), Qt.AlignRight | Qt.AlignTop, right_percent_str
    )

  def _get_round_rect_path(self, rect, radius):
    from PySide6.QtGui import QPainterPath

    path = QPainterPath()
    path.addRoundedRect(rect, radius, radius)
    return path

  def update_bar_display(self):
    setting_json = load_json(DISPLAY_SETTING_JSON_PATH)
    self.is_white_first = setting_json[IS_WHITE_FIRST_KEY]
    self.bar_width = setting_json[WINRATE_BAR_WIDTH_KEY]
    self.bar_height = setting_json[WINRATE_BAR_HEIGHT_KEY]
    self.resize(self.bar_width, self.bar_height)

  def closeEvent(self, event: QCloseEvent):
    close_window(WINRATE_BAR_KEY)
    event.accept()
