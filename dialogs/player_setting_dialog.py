from PySide6.QtCore import Signal
from PySide6.QtWidgets import QDialog, QHBoxLayout, QPushButton, QVBoxLayout

from small_widgets.labeled_input_widget import LabeledInputWidget


class PlayerSettingDialog(QDialog):
  def __init__(self, parent=None):
    super().__init__(parent)
    self.setWindowTitle("Player Selection")
    self.setMinimumSize(200, 200)

    # 메인 레이아웃 (Vertical)
    layout = QVBoxLayout(self)

    self.black_input = LabeledInputWidget("흑", "", False, self)
    self.white_input = LabeledInputWidget("백", "", False, self)
    layout.addWidget(self.black_input)
    layout.addWidget(self.white_input)

    # 확인 버튼 (Action Buttons) ---
    btn_layout = QHBoxLayout()
    self.cnf_btn = QPushButton("확인")
    btn_layout.addWidget(self.cnf_btn)
    layout.addLayout(btn_layout)

    # 시그널 연결 (Event Handling)
    self.cnf_btn.clicked.connect(self.confirm)  # 창 닫으면서 'OK' 반환

  change_player_signal = Signal(str, str)

  def confirm(self):
    if self.focusWidget():
      self.focusWidget().clearFocus()
    black = self.black_input.text().strip()
    white = self.white_input.text().strip()
    self.change_player_signal.emit(black, white)
    self.accept()
