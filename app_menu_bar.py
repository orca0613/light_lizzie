# menu_bar.py
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenuBar


class AppMenuBar(QMenuBar):
  def __init__(self, parent, controller):
    super().__init__(parent)
    self.controller = controller  # 중재자 Controller 주입받음

    # 메뉴 초기화 수행
    self._init_katago_path_menu()
    self._init_setting_menu()

  def _init_katago_path_menu(self):
    """카타고 경로 관련 메뉴 모듈화"""
    katago_path_menu = self.addMenu("카타고 경로 설정")

    katago_path_action = QAction("카타고 실행 파일 선택", self)
    model_path_action = QAction("가중치 모델 선택", self)
    config_path_action = QAction("컨피그 파일 선택", self)

    exit_action = QAction("종료", self)
    exit_action.triggered.connect(self.parent().close)  # 메인 윈도우 종료

    katago_path_action.triggered.connect(self.controller.set_katago_path)
    model_path_action.triggered.connect(self.controller.set_model_path)
    config_path_action.triggered.connect(self.controller.set_config_path)

    katago_path_menu.addAction(katago_path_action)
    katago_path_menu.addAction(model_path_action)
    katago_path_menu.addAction(config_path_action)

  def _init_setting_menu(self):
    """세팅 관련 메뉴 모듈화"""
    setting_menu = self.addMenu("환경 설정")

    katago_setting_action = QAction("카타고 옵션 설정", self)
    display_setting_action = QAction("디스플레이 옵션 설정", self)
    player_setting_action = QAction("플레이어 설정", self)
    window_setting_action = QAction("윈도우 설정", self)

    katago_setting_action.triggered.connect(self.controller.open_katago_setting_dialog)
    display_setting_action.triggered.connect(
      self.controller.open_display_setting_dialog
    )
    player_setting_action.triggered.connect(self.controller.open_player_setting_dialog)
    window_setting_action.triggered.connect(self.controller.open_window_setting_dialog)

    setting_menu.addAction(katago_setting_action)
    setting_menu.addAction(display_setting_action)
    setting_menu.addAction(player_setting_action)
    setting_menu.addAction(window_setting_action)
