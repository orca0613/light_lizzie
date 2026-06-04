from collections import Counter
from typing import List

import pandas as pd
from PySide6.QtWidgets import QMainWindow
from PySide6.QtGui import QCloseEvent, QFont, QPainter, QColor
from PySide6.QtCore import QRectF, Qt

from api import get_move_data
from constants import BOARD_SIZE_KEY, DISPLAY_SETTING_JSON_PATH, OPENING_BOARD_KEY
from helper import close_window, get_past_num_date, load_json

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


class OpeningDataBoard(QMainWindow):
  def __init__(self):
    super().__init__()
    self.setWindowTitle("Opening Data Overlay")
    self.board_size = 0
    self.margin = 0
    self.update_board_display() # 기본 크기 설정 (조절 가능)
    self.grid_size = 19
    self.black_code = 0
    self.white_code = 0
    
    # 1. 테두리 없는 창 생성 및 작업 표시줄에서 숨김 (선택)
    # self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
    
    # 2. ★ 핵심: 창 배경을 완전히 투명하게 설정
    self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
    
    self.opening_data = []
    self.black_data = None
    self.white_data = None
    self.gt = 2
    self.ref_date = get_past_num_date(5, 0)
    self.ps = "0"
    self.move_number = 0


  def update_black_data(self, player_code):
    if player_code == self.black_code:
      return
    opening_move_data = get_move_data(player_code)
    self.black_data = pd.DataFrame(opening_move_data)
    self.update_position(self.ps, self.move_number)


  def update_white_data(self, player_code):
    if player_code == self.white_code:
      return
    opening_move_data = get_move_data(player_code)
    self.white_data = pd.DataFrame(opening_move_data)
    self.update_position(self.ps, self.move_number)
    

  def update_position(self, ps: str, move_number: int):
    self.ps = ps
    self.move_number = move_number
    if move_number % 2:
      if self.white_data is None:
        return
      mv_series = self.white_data.loc[
        (self.white_data["dt"] >= self.ref_date) &
        (self.white_data["ps"] == ps),
        "mv"
      ]
      self._update_opening_data(mv_series)
    else:
      if self.black_data is None:
        return 
      mv_series = self.black_data.loc[
        (self.black_data["dt"] >= self.ref_date) &
        (self.black_data["ps"] == ps),
        "mv"
      ]
      self._update_opening_data(mv_series)
    # self.update() # 화면을 다시 그리도록 요청 (paintEvent 트리거)

  def _update_opening_data(self, series):
    total_count = len(series)
    counter = series.value_counts()
    self.opening_data = []
    for key, value in counter.items():
      self.opening_data.append((key, value, (value / total_count) * 100))
    self.update()




  def paintEvent(self, event):

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

    for loc, cnt, freq in self.opening_data:
      x, y = loc % 19, loc // 19
      # 실제 그릴 중심점 픽셀 좌표 계산
      center_x = self.margin + x * cell_size
      center_y = self.margin + y * cell_size
      circle_color = get_color_by_frequency(freq)

      radius = cell_size * 0.45
      move_rect = QRectF(center_x - radius, center_y - radius, radius * 2, radius * 2)

      # 1. 커스텀 컬러 및 투명도 설정 (Red, Green, Blue, Alpha)
      # Alpha 값은 0(완전 투명) ~ 255(완전 불투명) 사이로 조절합니다.

      painter.setBrush(circle_color)
      
      # 원 테두리 색상 설정 (원하는 경우 테두리는 투명하게 없앨 수도 있습니다: Qt.PenStyle.NoPen)
      painter.setPen(circle_color) 
      
      painter.drawEllipse(move_rect)

      # 1. 표시할 각각의 변수 설정
      cnt_text = str(cnt)      # 첫 번째 줄에 들어갈 변수
      freq_text = str(round(freq, 1)) + "%"   # 두 번째 줄에 들어갈 변수

      # 2. 폰트 설정 (두 줄이 들어가므로 크기를 기존보다 조금 줄이는 것이 좋습니다)
      cnt_font = QFont("Arial", int(cell_size * 0.3)) 
      painter.setFont(cnt_font)
      painter.setPen(Qt.GlobalColor.black)

      # 3. 영역 쪼개기 (기존 사각형의 높이를 절반으로 나누기)
      half_height = move_rect.height() / 2

      # 상단 줄 영역 (기존 사각형의 상단 절반)
      top_rect = QRectF(
        move_rect.left(), 
        move_rect.top(), 
        move_rect.width(), 
        half_height
      )

      # 하단 줄 영역 (기존 사각형의 하단 절반)
      bottom_rect = QRectF(
        move_rect.left(), 
        move_rect.top() + half_height, 
        move_rect.width(), 
        half_height
      )

      # 4. 각각의 영역에 변수 출력 (정중앙 정렬)
      painter.drawText(top_rect, Qt.AlignmentFlag.AlignCenter, cnt_text)

      # 2. 폰트 설정 (두 줄이 들어가므로 크기를 기존보다 조금 줄이는 것이 좋습니다)
      freq_font = QFont("Arial", int(cell_size * 0.2)) 
      painter.setFont(freq_font)
      painter.setPen(Qt.GlobalColor.black)

      painter.drawText(bottom_rect, Qt.AlignmentFlag.AlignCenter, freq_text)


  def update_board_display(self):
    setting_json = load_json(DISPLAY_SETTING_JSON_PATH)
    self.board_size = setting_json[BOARD_SIZE_KEY]
    self.margin = self.board_size / 20
    self.resize(self.board_size, self.board_size)


  def closeEvent(self, event: QCloseEvent):
    close_window(OPENING_BOARD_KEY)
    event.accept()