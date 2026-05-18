from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QRadioButton, QButtonGroup)
from PySide6.QtCore import Qt, Signal

from constants import BAR_OPTIONS, BOARD_SIZE_KEY, DISPLAY_SETTING_JSON_PATH, IS_WHITE_FIRST_KEY, KOMI_KEY, MAX_ANALYSIS_TIME_KEY, MAX_VISIT_KEY, RULE_KEY, RULES, KATAGO_SETTING_JSON_PATH, WIN_RATE_BAR_HEIGHT_KEY, WIN_RATE_BAR_WIDTH_KEY
from helper import load_json, update_json

class DisplaySettingDialog(QDialog):
  def __init__(self, parent=None):
    super().__init__(parent)
    self.setWindowTitle("Display Setting")
    self.setMinimumSize(200, 200)
    self.setting_json = load_json(DISPLAY_SETTING_JSON_PATH)
    self.changed = False
    
    # 메인 레이아웃 (Vertical)
    layout = QVBoxLayout(self)
    
    # 라디오 버튼 (그래프 옵션 설정) ---
    bar_option_layout = QHBoxLayout()
    bar_option_layout.setAlignment(Qt.AlignmentFlag.AlignJustify)
    bar_option_layout.addStretch(1)
    bar_option_layout.addWidget(QLabel("승률 바 표시 옵션"))
    bar_option_layout.addStretch(2)
    
    self.bar_option_radio_group = QButtonGroup(self)
    for i, text in enumerate(BAR_OPTIONS):
      radio = QRadioButton(text)
      radio.setChecked(self.setting_json[IS_WHITE_FIRST_KEY] == bool(i))
      self.bar_option_radio_group.addButton(radio, i)
      bar_option_layout.addWidget(radio)
      bar_option_layout.addStretch(2)
    bar_option_layout.addStretch(1)
    self.bar_option_radio_group.idClicked.connect(self.update_bar_option)
    layout.addLayout(bar_option_layout)

    # 보드 사이즈 레이아웃

    board_size_layout = QHBoxLayout()
    board_size_layout.addWidget(QLabel("보드 사이즈"))
    self.board_size_input = QLineEdit()
    self.board_size_input.setText(str(self.setting_json[BOARD_SIZE_KEY]))
    board_size_layout.addWidget(self.board_size_input)
    layout.addLayout(board_size_layout)

    # 승률 그래프 넓이 레이아웃

    winrate_bar_width_layout = QHBoxLayout()
    winrate_bar_width_layout.addWidget(QLabel("승률 그래프 넓이"))
    self.bar_width_input = QLineEdit()
    self.bar_width_input.setText(str(self.setting_json[WIN_RATE_BAR_WIDTH_KEY]))
    winrate_bar_width_layout.addWidget(self.bar_width_input)
    layout.addLayout(winrate_bar_width_layout)

    # 승률 그래프 높이 레이아웃

    winrate_bar_height_layout = QHBoxLayout()
    winrate_bar_height_layout.addWidget(QLabel("승률 그래프 높이"))
    self.bar_height_input = QLineEdit()
    self.bar_height_input.setText(str(self.setting_json[WIN_RATE_BAR_HEIGHT_KEY]))
    winrate_bar_height_layout.addWidget(self.bar_height_input)
    layout.addLayout(winrate_bar_height_layout)
    
    # 확인 버튼 (Action Buttons) ---
    btn_layout = QHBoxLayout()
    self.cnf_btn = QPushButton("확인")
    btn_layout.addWidget(self.cnf_btn)

    layout.addLayout(btn_layout)

    # 시그널 연결 (Event Handling)
    self.cnf_btn.clicked.connect(self.confirm) # 창 닫으면서 'OK' 반환
  
  update_display_setting_signal = Signal()

  def update_rule(self, idx: int):
    self.changed = True
    self.setting_json[RULE_KEY] = RULES[idx]
    komi = 7.5 if idx else 6.5
    self.setting_json[KOMI_KEY] = komi
    self.komi_input.setText(str(komi))
    return
  

  def update_bar_option(self, idx: int):
    self.changed = True
    self.setting_json[IS_WHITE_FIRST_KEY] = bool(idx)
    return
  

  def update_setting_json(self, key: str, val: int | str):
    self.changed = True
    self.setting_json[key] = val
    return
  

  def confirm(self):
    try:
      board_size = int(self.board_size_input.text().strip())
      bar_width = int(self.bar_width_input.text().strip())
      bar_height = int(self.bar_height_input.text().strip())

      if board_size != self.setting_json[BOARD_SIZE_KEY]:
        self.update_setting_json(BOARD_SIZE_KEY, board_size)
      if bar_width != self.setting_json[WIN_RATE_BAR_WIDTH_KEY]:
        self.update_setting_json(WIN_RATE_BAR_WIDTH_KEY, bar_width)
      if bar_height != self.setting_json[WIN_RATE_BAR_HEIGHT_KEY]:
        self.update_setting_json(WIN_RATE_BAR_HEIGHT_KEY, bar_height)

    except ValueError as e:
      # 사용자가 숫자가 아닌 문자(예: "abc")를 입력했을 때 에러 방지 예외처리
      print(e)
      return # 저장하지 않고 함수 종료 (창 안 닫힘)
    update_json(DISPLAY_SETTING_JSON_PATH, self.setting_json)
    if self.changed:
      self.update_display_setting_signal.emit()
    self.accept()