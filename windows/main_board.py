from PySide6.QtWidgets import QMainWindow
from PySide6.QtGui import QCloseEvent, QKeySequence, QPainter, QColor, QPen, QShortcut
from PySide6.QtCore import QPointF, QRectF, Qt, Signal

from app_menu_bar import AppMenuBar
from constants import BOARD_SIZE_KEY, DISPLAY_SETTING_JSON_PATH
from helper import load_json
from logic import play_move
from menu_controller import MenuController

class MainBoard(QMainWindow):
  def __init__(self):
    super().__init__()
    self.board_size = 0
    self.margin = 0
    self.update_board_display()
    self.setWindowTitle("Main Board")
    self.grid_size = 19
    self.move_number = 0
    self.history = [{}]
    self.undo_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Backspace), self)
    self.undo_shortcut.activated.connect(self.undo)

    self.menu_controller = MenuController(self)
    self.menu_bar = AppMenuBar(self, self.menu_controller)
    self.setMenuBar(self.menu_bar)

  
  clicked_pos = Signal(int, int) # 클릭된 x, y 좌표를 내보내는 신호
  undo_signal = Signal()
  update_katago_path_signal = Signal()
  update_katago_setting_signal = Signal()
  update_display_setting_signal = Signal()
  update_player_name_signal = Signal(str, str)
  closed_signal = Signal()


  def paintEvent(self, event):
    painter = QPainter(self)
    # 안티앨리어싱은 필수입니다.
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

    # 1. 배경색 (나무판 느낌)
    painter.setBrush(QColor(220, 179, 92))
    painter.drawRect(self.rect())

    # 1. 격자 및 보드 계산 (float 유지)
    rect_f = QRectF(self.rect())
    margin = float(self.margin)
    grid_count = self.grid_size - 1
    
    # 보드 영역 계산
    board_rect = rect_f.adjusted(margin, margin, -margin, -margin)
    cell_size = min(board_rect.width(), board_rect.height()) / grid_count
    self.cell_size = cell_size # 나중에 클릭 이벤트에서 쓰기 위해 저장

    # 2. 격자 그리기 (정밀도 보정)
    pen = QPen(Qt.GlobalColor.black, 1.0)
    painter.setPen(pen)
    
    for i in range(self.grid_size):
      pos = margin + i * cell_size
      # 가로선: (시작X, Y, 끝X, Y)
      painter.drawLine(QPointF(margin, pos), QPointF(margin + grid_count * cell_size, pos))
      # 세로선: (X, 시작Y, X, 끝Y)
      painter.drawLine(QPointF(pos, margin), QPointF(pos, margin + grid_count * cell_size))

    
    # 3. 화점(Star points) 그리기
    painter.setBrush(Qt.black)
    radius = cell_size * 0.1
    stars = [3, 9, 15]
    for row in stars:
      for col in stars:
        px = margin + col * self.cell_size
        py = margin + row * self.cell_size
        flower_point_rect = QRectF(px - radius, py - radius, radius * 2, radius * 2)
        painter.drawEllipse(flower_point_rect)

    # 3. 돌 그리기 (중심점 완벽 일치)
    stones = self.history[self.move_number]
    for l, color in stones.items():
      row, col = divmod(l, 19)
      
      # 교차점의 정확한 실수 좌표
      cx = margin + col * cell_size
      cy = margin + row * cell_size
      
      # 반지름 설정
      radius = cell_size * 0.45 if color != "K" else cell_size * 0.1
      
      # [핵심] QRectF를 사용하여 중심점을 기준으로 정확히 외접하는 사각형 정의
      # QRectF(중심X - 반지름, 중심Y - 반지름, 지름, 지름)
      stone_rect = QRectF(cx - radius, cy - radius, radius * 2, radius * 2)

      if color == "B":
        painter.setBrush(Qt.GlobalColor.black)
        painter.setPen(QPen(Qt.GlobalColor.black, 1))
      elif color == "W":
        painter.setBrush(Qt.GlobalColor.white)
        # 백돌이 선 위에 떠 있는 느낌을 주려면 0.5~1px의 검은 테두리가 필수입니다.
        painter.setPen(QPen(Qt.GlobalColor.black, 1))
      else:
        continue

      painter.drawEllipse(stone_rect)
  

  def undo(self):
    if not self.move_number:
      return
    self.move_number -= 1
    self.history.pop()
    self.repaint()
    self.undo_signal.emit()


  def mousePressEvent(self, event):
    # 클릭한 위치를 바둑판 좌표로 변환
    x = round((event.position().x() - self.margin) / self.cell_size)
    y = round((event.position().y() - self.margin) / self.cell_size)
    if not (0 <= y < 19 and 0 <= x < 19):
      return
    stones = self.history[self.move_number]
    l = y * 19 + x
    if (l < 0) or (l > 360) or (l in stones):
      return
    color = "W" if self.move_number % 2 else "B"
    new_stones = play_move(stones, l, color)
    if l not in new_stones:
      return
    self.history.append(new_stones)
    self.move_number += 1
    self.repaint()
        
    # 2. 메인 윈도우에 클릭 신호 발생 (엔진 전달용)
    self.clicked_pos.emit(x, y)

  
  def update_katago_path(self):
    self.update_katago_path_signal.emit()


  def update_katago_setting(self):
    self.update_katago_setting_signal.emit()


  def update_display_setting(self):
    self.update_display_setting_signal.emit()


  def update_board_display(self):
    setting_json = load_json(DISPLAY_SETTING_JSON_PATH)
    self.board_size = setting_json[BOARD_SIZE_KEY]
    self.margin = self.board_size / 20
    self.resize(self.board_size, self.board_size)


  def closeEvent(self, event: QCloseEvent):
    """창이 닫힐 때 PySide6가 자동으로 호출하는 함수"""
    self.closed_signal.emit()  # 컨트롤러에게 신호 발송
    event.accept()             # 창 닫기 승인


  def update_player_name(self, black: str, white: str):
    self.update_player_name_signal.emit(black, white)
