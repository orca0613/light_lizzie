from PySide6.QtGui import QFont
from PySide6.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QVBoxLayout, QWidget

from helper import get_color_by_score


class AnalysisBarWidget(QWidget):
  def __init__(self, title: str):
    super().__init__()
    self.title = title
    self.unit = "집" if title == "예상 스코어 변화" else "%"
    self.init_ui()

  def init_ui(self):
    # 메인 레이아웃 (위젯 자체의 여백을 최소화하여 컴팩트하게 구성)
    layout = QVBoxLayout(self)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(6)

    # 상단 타이틀 레이아웃 (텍스트 가로 정렬)
    title_layout = QHBoxLayout()

    self.title_label = QLabel(self.title)
    self.title_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))

    self.val_label = QLabel("0%")
    self.val_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))

    title_layout.addWidget(self.title_label)
    title_layout.addStretch()
    title_layout.addWidget(self.val_label)
    layout.addLayout(title_layout)

    # 하단 프로그레스 바 설정
    self.bar = QProgressBar()
    self.bar.setFixedHeight(15)
    self.bar.setTextVisible(False)
    layout.addWidget(self.bar)

  def update_value(self, val: float, normalized_score: float):
    """외부에서 실시간 데이터나 초기값을 주입할 때 호출하는 핵심 함수"""
    # 1. 점수 정규화 및 컬러 추출

    color = get_color_by_score(normalized_score)

    # 2. 텍스트 값 및 포인트 컬러 업데이트
    self.val_label.setText(f"{round(val, 1)}{self.unit}")
    self.val_label.setStyleSheet(f"color: {color};")

    # 3. 프로그레스 바 값 및 스타일시트(f-string 중괄호 이중화) 적용
    self.bar.setValue(int(normalized_score))
    self.bar.setStyleSheet(f"""
      QProgressBar {{
        border: none;
        background-color: #333338;
        border-radius: 7px;
      }}
      QProgressBar::chunk {{
        background-color: {color};
        border-radius: 7px;
      }}
    """)
