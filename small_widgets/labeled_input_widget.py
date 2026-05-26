from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QLineEdit
from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtCore import QRegularExpression 

class LabeledInputWidget(QWidget):
  def __init__(self, label_text: str, default_value: str = "", only_number: bool = False, parent=None):
    super().__init__(parent)
    
    # 1. 레이아웃 설정 (부모와 정렬이 맞도록 마진 제거)
    layout = QHBoxLayout(self)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(10) # 라벨과 인풋창 사이 간격
    
    # 2. 라벨 추가
    self.label = QLabel(label_text)
    layout.addWidget(self.label)
    
    # 3. 입력창(QLineEdit) 추가 및 설정
    self.input_field = QLineEdit(default_value)
      
    # 💡 옵션: 숫자만 입력받아야 하는 경우 (예: 점수, 베팅 금액 등)
    if only_number:
      reg_ex = QRegularExpression(r"^[0-9]*(?:\.[0-9]*)?$")
      validator = QRegularExpressionValidator(reg_ex, self)
      self.input_field.setValidator(validator)
      
    layout.addWidget(self.input_field)
      
  def text(self) -> str:
    """부모 창에서 유저가 입력한 값을 str 타입으로 바로 가져가는 메서드"""
    return self.input_field.text().strip()
  
  def set_text(self, text: str):
    """부모 창에서 코드로 값을 넣어주고 싶을 때 사용"""
    self.input_field.setText(text)
    
  def clear(self):
    """입력창 초기화"""
    self.input_field.clear()