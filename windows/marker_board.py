
from PySide6.QtWidgets import QMainWindow
from PySide6.QtGui import QCloseEvent, QPainter
from PySide6.QtCore import QRectF, Qt

from constants import BOARD_SIZE_KEY, DISPLAY_SETTING_JSON_PATH, MARKER_BOARD_KEY
from helper import close_window, load_json

class MarkerBoard(QMainWindow):
  def __init__(self):
    super().__init__()
    self.setWindowTitle("Go Move Overlay")
    self.board_size = 0
    self.margin = 0
    self.update_board_display() # 기본 크기 설정 (조절 가능)
    self.grid_size = 19
    
    # 1. 테두리 없는 창 생성 및 작업 표시줄에서 숨김 (선택)
    # self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
    
    # 2. ★ 핵심: 창 배경을 완전히 투명하게 설정
    self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
    
    # 마지막 착점 좌표 보관용 변수 (초기값은 없음)
    self.last_move = None  # 예: (x_index, y_index) -> (3, 4)

  def set_last_move(self, x, y):
    """메인 창이나 카타고 분석부에서 호출하여 좌표를 갱신하는 메서드"""
    if x < 0 or y < 0:
      self.last_move = None
    else:
      self.last_move = (x, y)
    self.update() # 화면을 다시 그리도록 요청 (paintEvent 트리거)

  def paintEvent(self, event):
    """투명한 도화지 위에 체크표시만 그리는 내장 이벤트"""
    if self.last_move is None:
      return

    painter = QPainter(self)
    # 안티앨리어싱으로 부드럽게 그리기
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # 1. 격자 및 보드 계산 (float 유지)
    rect_f = QRectF(self.rect())
    margin = float(self.margin)
    grid_count = self.grid_size - 1
    
    # 보드 영역 계산
    board_rect = rect_f.adjusted(margin, margin, -margin, -margin)
    cell_size = board_rect.width() / grid_count
    self.cell_size = cell_size # 나중에 클릭 이벤트에서 쓰기 위해 저장

    x, y = self.last_move
    
    # 실제 그릴 중심점 픽셀 좌표 계산
    center_x = self.margin + x * cell_size
    center_y = self.margin + y * cell_size

    radius = cell_size * 0.2
    move_rect = QRectF(center_x - radius, center_y - radius, radius * 2, radius * 2)

    painter.setBrush(Qt.GlobalColor.red)
    painter.setPen(Qt.GlobalColor.red)
    painter.drawEllipse(move_rect)


  def update_board_display(self):
    setting_json = load_json(DISPLAY_SETTING_JSON_PATH)
    self.board_size = setting_json[BOARD_SIZE_KEY]
    self.margin = self.board_size / 20
    self.resize(self.board_size, self.board_size)


  def closeEvent(self, event: QCloseEvent):
    close_window(MARKER_BOARD_KEY)
    event.accept()