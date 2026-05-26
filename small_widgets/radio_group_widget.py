from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QRadioButton, QButtonGroup
from PySide6.QtCore import Qt

class RadioGroupWidget(QWidget):
  def __init__(self, width: int, title: str, options: list, default_index: int, on_clicked_callback, parent=None):
    super().__init__(parent)

    self.setFixedWidth(width)
    
    # 1. 레이아웃 설정
    layout = QHBoxLayout(self)
    layout.setContentsMargins(0, 0, 0, 0) 
    
    # 기본 스페이싱(여백)을 0으로 만들어 스트레치 엔진이 간격을 온전히 통제하게 합니다.
    layout.setSpacing(0) 
    
    # [변경] 맨 앞의 stretch 제거 (타이틀 라벨이 왼쪽 벽에 딱 붙음)
    layout.addWidget(QLabel(title))
    
    # 타이틀과 첫 번째 라디오 버튼 사이를 띄워줍니다.
    layout.addStretch(1) 
    
    # 2. QButtonGroup 생성 및 옵션 버튼 배치
    self.radio_group = QButtonGroup(self)
    
    last_index = len(options) - 1
    for i, text in enumerate(options):
      radio = QRadioButton(text)
      radio.setChecked(i == default_index)
      
      self.radio_group.addButton(radio, i)
      layout.addWidget(radio)
      
      # [변경] 마지막 라디오 버튼 뒤에는 stretch를 넣지 않습니다. 
      # 그래야 마지막 버튼이 오른쪽 벽에 딱 붙습니다.
      if i < last_index:
        layout.addStretch(1) # 내부 위젯들 사이에만 동일한 가중치(1)로 공백 배치
        
    # 3. 시그널 연결
    self.radio_group.idClicked.connect(on_clicked_callback)

  def checkedId(self) -> int:
    return self.radio_group.checkedId()