import sys
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QApplication
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
from PySide6.QtGui import QCloseEvent, QPainter
from PySide6.QtCore import Qt

from constants import DISPLAY_SETTING_JSON_PATH, WINRATE_CHART_HEIGHT_KEY, WINRATE_CHART_KEY, WINRATE_CHART_WIDTH_KEY
from helper import close_window, load_json

# 1. 기존 차트 컴포넌트 (그대로 유지)
class WinrateChart(QChartView):
  def __init__(self, width, height):
    super().__init__()
    self.setFixedSize(width, height)
    self.series = QLineSeries()
    self.chart = QChart()
    
    self.chart.addSeries(self.series)
    self.chart.legend().hide()

    # X축 설정
    self.axis_x = QValueAxis()
    self.axis_x.setRange(0, 100)
    self.axis_x.setLabelFormat("%d")
    self.chart.addAxis(self.axis_x, Qt.AlignBottom)
    self.series.attachAxis(self.axis_x)

    # Y축 설정
    self.axis_y = QValueAxis()
    self.axis_y.setRange(0, 100)
    self.axis_y.setLabelFormat("%d%%  ")
    self.axis_y.setTickCount(3)

    self.axis_y.setGridLineVisible(True) 
    self.chart.addAxis(self.axis_y, Qt.AlignLeft)
    self.series.attachAxis(self.axis_y)

    # 축의 진한 외곽선 숨기기
    self.axis_y.setLineVisible(False)
    self.axis_x.setLineVisible(False)

    self.setChart(self.chart)
    self.setRenderHint(QPainter.Antialiasing)

  def update_data(self, winrate_history: list):
    self.series.clear()
    for i, winrate in enumerate(winrate_history):
      self.series.append(i, winrate)

    if len(winrate_history) > self.axis_x.max():
      self.axis_x.setRange(0, len(winrate_history) + 20)


# 2. 💡 새 창으로 띄우기 위한 QMainWindow 클래스
class WinrateChartWindow(QMainWindow):
  def __init__(self):
    # 부모 창이 꺼져도 이 창은 독립적으로 유지되도록 독립 윈도우 플래그 설정
    super().__init__()
    self.setting_json = load_json(DISPLAY_SETTING_JSON_PATH)
    chart_width = self.setting_json[WINRATE_CHART_WIDTH_KEY]
    chart_height = self.setting_json[WINRATE_CHART_HEIGHT_KEY]
    self.winrate_history = [50]
    
    # 창 제목 및 초기 설정
    self.setWindowTitle("Winrate Chart")
    
    # 메인 윈도우는 중앙 위젯(Central Widget)이 필수입니다.
    central_widget = QWidget(self)
    self.setCentralWidget(central_widget)
    
    # 레이아웃에 만들어둔 차트 컴포넌트 장착
    layout = QVBoxLayout(central_widget)
    layout.setContentsMargins(0, 0, 0, 0)
    
    self.chart_view = WinrateChart(chart_width, chart_height)
    layout.addWidget(self.chart_view)
    
    # 창 크기를 차트 크기에 딱 맞게 자동 조절
    self.adjustSize()


  def play_move(self):
    last_winrate = self.winrate_history[-1]
    self.winrate_history.append(last_winrate)
    self.chart_view.update_data(self.winrate_history)
    return
  

  def undo(self):
    if len(self.winrate_history) > 1:
      self.winrate_history.pop()
      self.chart_view.update_data(self.winrate_history)
      return
    

  def update_winrate(self, winrate: int):
    """외부(부모 창 등)에서 데이터를 넘겨받아 그래프를 갱신하는 창구"""
    self.winrate_history[-1] = winrate
    self.chart_view.update_data(self.winrate_history)


  def closeEvent(self, event: QCloseEvent):
    close_window(WINRATE_CHART_KEY)
    event.accept()
