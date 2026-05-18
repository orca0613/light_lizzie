from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
from PySide6.QtGui import QColor, QPainter
from PySide6.QtCore import QMargins, Qt

class WinRateChart(QChartView):
  def __init__(self, width):
    super().__init__()
    self.setFixedSize(width, width)
    self.series = QLineSeries()
    self.chart = QChart()
    
    # 차트 설정
    self.chart.addSeries(self.series)
    self.chart.legend().hide()

    # X축 설정 (수순)
    self.axis_x = QValueAxis()
    self.axis_x.setRange(0, 100) # 기본 100수까지
    self.axis_x.setLabelFormat("%d")
    self.chart.addAxis(self.axis_x, Qt.AlignBottom)
    self.series.attachAxis(self.axis_x)

    # Y축 설정
    self.axis_y = QValueAxis()
    self.axis_y.setRange(0, 100)
    self.axis_y.setLabelFormat("%d%%  ")
    self.axis_y.setTickCount(3)  # 0, 50, 100 표시

    # 그리드 선을 연하게 만들어 레이블이 돋보이게 함
    self.axis_y.setGridLineVisible(True) 
    self.axis_y.setLineVisible(True) # 축 자체 선 표시

    self.chart.addAxis(self.axis_y, Qt.AlignLeft)
    self.series.attachAxis(self.axis_y)

    # 축 자체의 진한 선을 숨깁니다 (그리드 선만 남음)
    self.axis_y.setLineVisible(False)
    self.axis_x.setLineVisible(False)

    self.setChart(self.chart)
    self.setRenderHint(QPainter.Antialiasing)

  def update_data(self, winrate_history: list):
    """승률 리스트를 받아 그래프를 갱신합니다."""
    self.series.clear()
    for i, (winrate, _) in enumerate(winrate_history):
      self.series.append(i, winrate)
  
    # 수순이 길어지면 X축 범위를 늘림
    if len(winrate_history) > self.axis_x.max():
      self.axis_x.setRange(0, len(winrate_history) + 20)