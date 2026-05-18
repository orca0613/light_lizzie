from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QRadioButton, QButtonGroup)
from PySide6.QtCore import Qt, Signal

from constants import IS_WHITE_FIRST_KEY, KOMI_KEY, MAX_ANALYSIS_TIME_KEY, MAX_VISIT_KEY, RULE_KEY, RULES, KATAGO_SETTING_JSON_PATH
from helper import load_json, update_json

class KatagoSettingDialog(QDialog):
  def __init__(self, parent=None):
    super().__init__(parent)
    self.setWindowTitle("Katago Setting")
    self.setMinimumSize(200, 200)
    self.setting_json = load_json(KATAGO_SETTING_JSON_PATH)
    self.changed = False
    
    # 메인 레이아웃 (Vertical)
    layout = QVBoxLayout(self)
    
    # 라디오 버튼 (규칙 설정) ---
    rule_layout = QHBoxLayout()
    rule_layout.setAlignment(Qt.AlignmentFlag.AlignJustify)
    rule_layout.addStretch(1)
    rule_layout.addWidget(QLabel("Rule"))
    rule_layout.addStretch(2)
    
    self.rule_radio_group = QButtonGroup(self)
    default_rule = self.setting_json[RULE_KEY]
    for i, text in enumerate(RULES):
      radio = QRadioButton(text)
      radio.setChecked(default_rule == text)
      self.rule_radio_group.addButton(radio, i)
      rule_layout.addWidget(radio)
      rule_layout.addStretch(2)
    rule_layout.addStretch(1)
    self.rule_radio_group.idClicked.connect(self.update_rule)
    layout.addLayout(rule_layout)

    # 덤(komi) 레이아웃

    komi_layout = QHBoxLayout()
    komi_layout.addWidget(QLabel("덤"))
    self.komi_input = QLineEdit()
    self.komi_input.setText(str(self.setting_json[KOMI_KEY]))
    komi_layout.addWidget(self.komi_input)
    layout.addLayout(komi_layout)

    # 비짓 카운트 레이아웃

    visit_count_layout = QHBoxLayout()
    visit_count_layout.addWidget(QLabel("비짓 카운트"))
    self.vc_input = QLineEdit()
    self.vc_input.setText(str(self.setting_json[MAX_VISIT_KEY]))
    visit_count_layout.addWidget(self.vc_input)
    layout.addLayout(visit_count_layout)

    # 분석 시간 레이아웃

    analysis_sec_layout = QHBoxLayout()
    analysis_sec_layout.addWidget(QLabel("분석 시간 (초)"))
    self.as_input = QLineEdit()
    self.as_input.setText(str(self.setting_json[MAX_ANALYSIS_TIME_KEY]))
    analysis_sec_layout.addWidget(self.as_input)
    layout.addLayout(analysis_sec_layout)
    
    # 확인 버튼 (Action Buttons) ---
    btn_layout = QHBoxLayout()
    self.cnf_btn = QPushButton("확인")
    btn_layout.addWidget(self.cnf_btn)

    layout.addLayout(btn_layout)

    # 시그널 연결 (Event Handling)
    self.cnf_btn.clicked.connect(self.confirm) # 창 닫으면서 'OK' 반환
  
  update_katago_setting_signal = Signal()

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
      visit_count = int(self.vc_input.text().strip())
      analysis_time = int(self.as_input.text().strip())
      komi = float(self.komi_input.text().strip())
      if visit_count != self.setting_json[MAX_VISIT_KEY]:
        self.update_setting_json(MAX_VISIT_KEY, visit_count)
      if analysis_time != self.setting_json[MAX_ANALYSIS_TIME_KEY]:
        self.update_setting_json(MAX_ANALYSIS_TIME_KEY, analysis_time)
      if komi != self.setting_json[KOMI_KEY]:
        self.update_setting_json(KOMI_KEY, komi)
    except ValueError:
      # 사용자가 숫자가 아닌 문자(예: "abc")를 입력했을 때 에러 방지 예외처리
      print("올바른 숫자를 입력해주세요.")
      return # 저장하지 않고 함수 종료 (창 안 닫힘)
    update_json(KATAGO_SETTING_JSON_PATH, self.setting_json)
    if self.changed:
      self.update_katago_setting_signal.emit()
    self.accept()