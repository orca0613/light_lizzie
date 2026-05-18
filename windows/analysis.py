import pandas as pd
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtGui import QFont

from analysis_bar import AnalysisBarWidget
from api import get_analysis_data
from helper import get_range_by_move_number, get_range_by_score, get_range_by_winrate, normalize_bluespot_score, normalize_delta_score, normalize_delta_winrate

class AnalysisWindow(QMainWindow):
  def __init__(self, color: str):
    super().__init__()
    self.setWindowTitle("AI Move Analysis")
    self.resize(250, 250)  # 방송 화면 구석에 배치하기 좋은 적당한 세로형 크기
    self.df = None
    
    # 크로마키나 투명을 적용할 수 있도록 배경 스타일 지정
    self.setStyleSheet("""
      QMainWindow {
        background-color: #1E1E24;
        color: #FFFFFF;
      }
      QLabel {
        color: #E0E0E0;
      }
    """)

    self.color = color
    
    # 메인 위젯 및 레이아웃 설정
    main_widget = QWidget()
    self.setCentralWidget(main_widget)
    layout = QVBoxLayout(main_widget)
    layout.setContentsMargins(20, 25, 20, 25)
    layout.setSpacing(20)

    # ----------------------------------------------------
    # 1. 상단: 기사 정보 영역 (흑/백 돌 표시 + 이름)
    # ----------------------------------------------------
    self.profile_layout = QHBoxLayout()
    
    # 돌 표시 (HTML 테그로 원형 아이콘 구현)
    self.stone_icon = QLabel()
    self.stone_icon.setFixedSize(24, 24)
    stone_color = "#000000" if self.color == "black" else "#FFFFFF"
    border_color = "#FFFFFF" if self.color == "black" else "#000000"
    # 기본값: 흑돌 (검은 원에 흰 테두리)
    self.stone_icon.setStyleSheet(f"background-color: {stone_color}; border: 1px solid {border_color}; border-radius: 12px;")
    
    self.name_label = QLabel()
    self.name_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))

    self.count_label = QLabel("0")
    self.count_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))

    self.profile_layout.addWidget(self.stone_icon)
    self.profile_layout.addWidget(self.name_label)
    self.profile_layout.addStretch()
    self.profile_layout.addWidget(self.count_label)
    layout.addLayout(self.profile_layout)

    # 구분선
    line = QWidget()
    line.setFixedHeight(1)
    line.setStyleSheet("background-color: #333333;")
    layout.addWidget(line)

    # ----------------------------------------------------
    # 2. 상단: 예상 승률 변동 
    # ----------------------------------------------------
    normalized_delta_winrate = normalize_delta_winrate(0)
    self.delta_winrate_bar = AnalysisBarWidget("예상 승률 변화")
    self.delta_winrate_bar.update_value(0, normalized_delta_winrate)
    layout.addWidget(self.delta_winrate_bar)

    # ----------------------------------------------------
    # 3. 중단: 예상 스코어 변동
    # ----------------------------------------------------
    normalized_delta_score = normalize_delta_score(0)
    self.delta_score_bar = AnalysisBarWidget("예상 스코어 변화")
    self.delta_score_bar.update_value(0, normalized_delta_score)
    layout.addWidget(self.delta_score_bar)

    # ----------------------------------------------------
    # 4. 하단: 블루스팟 적중 확률
    # ----------------------------------------------------
    normalized_bluespot_score = normalize_bluespot_score(0)
    self.bluespot_bar = AnalysisBarWidget("블루스팟 적중률")
    self.bluespot_bar.update_value(0, normalized_bluespot_score)
    layout.addWidget(self.bluespot_bar)
    
    layout.addStretch() # 아래쪽 여백 밀어내기


  def update_player(self, name: str, player_code: int):
    self.name_label.setText(name)
    if not player_code:
      return
    analysis_data = get_analysis_data(player_code)
    self.df = pd.DataFrame(analysis_data)


  def update_data(self, delta_winrate: float, delta_score: float, bluespot_ratio: float, count: int):
    normalized_delta_winrate = normalize_delta_winrate(delta_winrate)
    normalized_delta_score = normalize_delta_score(delta_score)
    normalized_bluespot_score = normalize_bluespot_score(bluespot_ratio)

    self.delta_winrate_bar.update_value(delta_winrate, normalized_delta_winrate)
    self.delta_score_bar.update_value(delta_score, normalized_delta_score)
    self.bluespot_bar.update_value(bluespot_ratio, normalized_bluespot_score)

    self.count_label.setText(str(count))


  def update_analysis_data(self, move_number: int, winrate: float, score: float, complexity: float):
    if self.df is None:
      return
    min_tn, max_tn = get_range_by_move_number(move_number)
    min_wr, max_wr = get_range_by_winrate(winrate)
    min_sc, max_sc = get_range_by_score(score)
    condition = (
      self.df["tn"].between(min_tn, max_tn) &
      self.df["wr"].between(min_wr, max_wr) &
      self.df["sc"].between(min_sc, max_sc)
    )

    sliced_df = self.df.loc[condition, ['dw', 'ds', 'dc', 'bs']]
    count = len(sliced_df)
    if not count:
      self.update_data(0, 0, 0, 0)
    delta_winrate = sliced_df["dw"].mean()
    delta_score = sliced_df["ds"].mean()
    bluespot_ratio = sliced_df["bs"].mean() * 100

    self.update_data(delta_winrate, delta_score, bluespot_ratio, count)

