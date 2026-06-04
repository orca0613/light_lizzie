from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCloseEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import QMainWindow

from app_menu_bar import AppMenuBar
from boards.main_board import MainBoard
from constants import BOARD_SIZE_KEY, DISPLAY_SETTING_JSON_PATH, ZOBRIST_JSON_PATH
from helper import load_json
from logic import play_move
from menu_controller import MenuController

zobrist_json = load_json(ZOBRIST_JSON_PATH)
black_zobrist_data = zobrist_json["black"]
white_zobrist_data = zobrist_json["white"]


class MainBoardWindow(QMainWindow):
  def __init__(self):
    super().__init__()
    self.board = MainBoard(self)
    self.board.clicked_pos.connect(self._play_move)
    self.setCentralWidget(self.board)
    self.setWindowTitle("Main Board")
    self.move_number = 0
    self.history = [{}]
    self.position = 0
    self.undo_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Backspace), self)
    self.undo_shortcut.activated.connect(self._undo)

    self.menu_controller = MenuController(self)
    self.menu_bar = AppMenuBar(self, self.menu_controller)
    self.setMenuBar(self.menu_bar)
    # self.update_background_cache()

  played_pos = Signal(int, int)
  clicked_pos = Signal(int, int)  # 클릭된 x, y 좌표를 내보내는 신호
  undo_signal = Signal()
  update_katago_path_signal = Signal()
  update_katago_setting_signal = Signal()
  update_display_setting_signal = Signal()
  update_player_name_signal = Signal(str, str)
  update_window_setting_signal = Signal()
  update_position_signal = Signal(str)
  closed_signal = Signal()

  def _undo(self):
    if not self.move_number:
      return
    self.move_number -= 1
    last_stones = self.history.pop()
    new_stones = self.history[-1]
    last_move = -1

    for key in last_stones.keys():
      if key not in new_stones:
        last_move = key
        last_color = last_stones[key]
    if last_color == "B" or last_color == "W":
      data = black_zobrist_data if last_color == "B" else white_zobrist_data
      self.position ^= data[last_move]
      self._send_position()
    self.board.set_stones(new_stones)
    self.undo_signal.emit()

  def _update_position(self, loc: int):
    data = black_zobrist_data if self.move_number % 2 else white_zobrist_data
    self.position ^= data[loc]
    self._send_position()

  def _send_position(self):
    ps_str = hex(self.position)[2:]
    self.update_position_signal.emit(ps_str)

  def _play_move(self, x: int, y: int):
    stones = self.history[self.move_number]
    loc = y * 19 + x
    if loc in stones:
      return
    color = "W" if self.move_number % 2 else "B"
    new_stones = play_move(stones, loc, color)
    if loc not in new_stones:
      return
    self.history.append(new_stones)
    self.board.set_stones(new_stones)
    self.move_number += 1
    self._update_position(loc)

    # 2. 메인 윈도우에 클릭 신호 발생 (엔진 전달용)
    self.clicked_pos.emit(x, y)
    self.played_pos.emit(x, y)

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

    board_rect_size = self.board_size - (self.margin * 2)
    self.cell_size = board_rect_size / self.grid_size
    self.resize(self.board_size, self.board_size)

  def closeEvent(self, event: QCloseEvent):
    """창이 닫힐 때 PySide6가 자동으로 호출하는 함수"""
    self.closed_signal.emit()  # 컨트롤러에게 신호 발송
    event.accept()  # 창 닫기 승인

  def update_player_name(self, black: str, white: str):
    self.update_player_name_signal.emit(black, white)

  def update_window_setting(self):
    self.update_window_setting_signal.emit()
