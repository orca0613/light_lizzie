from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton)
from PySide6.QtCore import Signal

from constants import IS_WHITE_FIRST_KEY, KOMI_KEY, MAX_ANALYSIS_TIME_KEY, MAX_VISIT_KEY, RULE_KEY, RULES, KATAGO_SETTING_JSON_PATH, UPDATE_CYCLE_KEY
from helper import load_json, update_json
from small_widgets.labeled_input_widget import LabeledInputWidget
from small_widgets.radio_group_widget import RadioGroupWidget

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
    rule_idx = 1 if self.setting_json[RULE_KEY] == "chinese" else 0
    rule_group = RadioGroupWidget(200, "규칙", RULES, rule_idx, self._update_rule, self)
    layout.addWidget(rule_group)

    # 덤(komi) 레이아웃

    self.komi_input = LabeledInputWidget("덤", str(self.setting_json[KOMI_KEY]), True, self)
    layout.addWidget(self.komi_input)

    # 비짓 카운트 레이아웃

    self.vc_input = LabeledInputWidget("비짓 카운트", str(self.setting_json[MAX_VISIT_KEY]), True, self)
    layout.addWidget(self.vc_input)

    # 분석 시간 레이아웃

    self.as_input = LabeledInputWidget("분석 시간", str(self.setting_json[MAX_ANALYSIS_TIME_KEY]), True, self)
    layout.addWidget(self.as_input)

    # 갱신 주기 레이아웃

    self.uc_input = LabeledInputWidget("갱신 주기", str(self.setting_json[UPDATE_CYCLE_KEY]), True, self)
    layout.addWidget(self.uc_input)
    
    # 확인 버튼 (Action Buttons) ---
    btn_layout = QHBoxLayout()
    self.cnf_btn = QPushButton("확인")
    btn_layout.addWidget(self.cnf_btn)

    layout.addLayout(btn_layout)

    # 시그널 연결 (Event Handling)
    self.cnf_btn.clicked.connect(self._confirm) # 창 닫으면서 'OK' 반환
  
  update_katago_setting_signal = Signal()

  def _update_rule(self, idx: int):
    self.changed = True
    self.setting_json[RULE_KEY] = RULES[idx]
    komi = 7.5 if idx else 6.5
    self.setting_json[KOMI_KEY] = komi
    self.komi_input.set_text(str(komi))
    return
  

  def _update_setting_json(self, key: str, val: int | str):
    self.changed = True
    self.setting_json[key] = val
    return
  

  def _check_update(self, key: str, val):
    if val != self.setting_json[key]:
      self._update_setting_json(key, val)


  def _confirm(self):
    try:
      komi = float(self.komi_input.text().strip())
      visit_count = int(self.vc_input.text().strip())
      analysis_time = int(self.as_input.text().strip())
      update_cycle = int(self.uc_input.text().strip())

      self._check_update(KOMI_KEY, komi)
      self._check_update(MAX_VISIT_KEY, visit_count)
      self._check_update(MAX_ANALYSIS_TIME_KEY, analysis_time)
      self._check_update(UPDATE_CYCLE_KEY, update_cycle)

    except ValueError:
      # 사용자가 숫자가 아닌 문자(예: "abc")를 입력했을 때 에러 방지 예외처리
      print("올바른 숫자를 입력해주세요.")
      return # 저장하지 않고 함수 종료 (창 안 닫힘)
    update_json(KATAGO_SETTING_JSON_PATH, self.setting_json)
    if self.changed:
      self.update_katago_setting_signal.emit()
    self.accept()