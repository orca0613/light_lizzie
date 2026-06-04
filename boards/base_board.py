from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QWidget

from constants import BOARD_SIZE_KEY, DISPLAY_SETTING_JSON_PATH
from helper import load_json


class BaseGoBoard(QWidget):
  def __init__(self, parent=None):
    super().__init__(parent)
    self.board_size = 0
    self.grid_size = 19
    self.margin = 0
    self.cell_size = 0.0
    self.transparent_mode = False
    self.background_cache = QPixmap()

    # 초기에 설정 파일로부터 고정된 바둑판 설정 수치를 로드합니다.
    self.load_display_settings()

  def load_display_settings(self):
    """설정 파일에서 보드 사이즈를 읽어와 기본 마진을 세팅하는 함수"""
    setting_json = load_json(DISPLAY_SETTING_JSON_PATH)
    self.board_size = setting_json[BOARD_SIZE_KEY]
    self.margin = self.board_size / 20

    # 💡 고정 크기 바둑판이라면 위젯 자체의 크기를 이 사이즈로 강제 고정해 주는 것이 좋습니다.
    self.setFixedSize(int(self.board_size), int(self.board_size))

  def set_transparent_mode(self, enabled: bool):
    """외부에서 투명 모드를 켜고 끌 수 있는 함수"""
    self.transparent_mode = enabled
    self.update_background_cache()  # 캐시 갱신
    self.update()  # 화면 다시 그리기

  def resizeEvent(self, event):
    """[⚠️ 필수] 창이 처음 켜지거나 크기가 바뀔 때 캐시를 그려내는 타이밍"""
    super().resizeEvent(event)
    self.update_background_cache()

  def update_background_cache(self):
    """고해상도 배경 캐시 생성"""
    # 아직 위젯 크기가 잡히지 않은 초기 상태라면 생략
    if self.size().isEmpty():
      return

    # 투명 모드라면 캐시를 만들지 않고 비워둡니다.
    if self.transparent_mode:
      self.background_cache = QPixmap()
      return

    # [나무판 모드일 때만 고해상도 캐시 생성]
    dpr = self.devicePixelRatioF()
    self.background_cache = QPixmap(self.width() * int(dpr), self.height() * int(dpr))
    self.background_cache.setDevicePixelRatio(dpr)

    cache_painter = QPainter(self.background_cache)
    cache_painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # 1. 배경 그리기
    cache_painter.setBrush(QColor(220, 179, 92))
    cache_painter.setPen(Qt.PenStyle.NoPen)
    cache_painter.drawRect(self.rect())

    # 정확한 격자 및 칸 크기 계산식 (float 유지)
    rect_f = QRectF(self.rect())
    margin = float(self.margin)
    grid_count = self.grid_size - 1  # 19줄이면 칸은 18개
    board_rect = rect_f.adjusted(margin, margin, -margin, -margin)

    # 가로 세로 중 좁은 영역 기준으로 칸 크기 결정
    self.cell_size = min(board_rect.width(), board_rect.height()) / grid_count

    # 2. 격자선 그리기
    pen = QPen(Qt.GlobalColor.black, 1.0)
    cache_painter.setPen(pen)
    for i in range(self.grid_size):
      pos = margin + i * self.cell_size
      # 가로선
      cache_painter.drawLine(
        QPointF(margin, pos), QPointF(margin + grid_count * self.cell_size, pos)
      )
      # 세로선
      cache_painter.drawLine(
        QPointF(pos, margin), QPointF(pos, margin + grid_count * self.cell_size)
      )

    # 3. 화점 그리기
    cache_painter.setBrush(Qt.GlobalColor.black)
    radius = self.cell_size * 0.1
    stars = [3, 9, 15]
    for row in stars:
      for col in stars:
        px = margin + col * self.cell_size
        py = margin + row * self.cell_size
        cache_painter.drawEllipse(
          QRectF(px - radius, py - radius, radius * 2, radius * 2)
        )

    cache_painter.end()
    self.update()  # 캐시 다 그렸으니 화면 갱신 요청

  def paintEvent(self, event):
    painter = QPainter(self)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # 1. 투명 모드가 아닐 때만 캐시된 배경 이미지를 그립니다.
    if not self.transparent_mode and not self.background_cache.isNull():
      painter.drawPixmap(0, 0, self.background_cache)

    # 2. 바둑판 위에 나타낼 "다양한 정보"는 자식 클래스에게 위임합니다.
    self.draw_overlay_info(painter)

  def draw_overlay_info(self, painter):
    """자식 클래스들이 각자 마다의 정보를 그리기 위해 오버라이딩할 함수"""
    pass
