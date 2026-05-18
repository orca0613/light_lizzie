from PySide6.QtWidgets import QFileDialog

from constants import KATAGO_VAR_PATH
from dialogs.display_setting_dialog import DisplaySettingDialog
from dialogs.katago_setting_dialog import KatagoSettingDialog
from dialogs.player_setting_dialog import PlayerSettingDialog
from helper import load_json, update_json

class MenuController:
  def __init__(self, main_window):
    self.main_window = main_window
    self.katago_setting_dialog = KatagoSettingDialog(self.main_window)
    self.display_setting_dialog = DisplaySettingDialog(self.main_window)
    self.player_setting_dialog = PlayerSettingDialog(self.main_window)
    
    self.katago_setting_dialog.update_katago_setting_signal.connect(self._set_katago_setting)
    self.display_setting_dialog.update_display_setting_signal.connect(self._set_display_setting)
    self.player_setting_dialog.change_player_signal.connect(self._set_player_setting)

  # 카타고 관련 경로 설정
  def set_katago_path(self):
    katago_path, _ = QFileDialog.getOpenFileName(self.main_window, "카타고 실행 파일 선택", "", "Exec (*.exe)")
    if not katago_path: 
      return
    self._edit_katago_path_json("exe", katago_path)


  def set_model_path(self):
    model_path, _ = QFileDialog.getOpenFileName(self.main_window, "가중치 모델 선택", "", "Model (*.bin.gz)")
    if not model_path: 
      return
    self._edit_katago_path_json("model", model_path)


  def set_config_path(self):
    config_path, _ = QFileDialog.getOpenFileName(self.main_window, "컨피그 파일 선택", "", "Config (*.cfg)")
    if not config_path: 
      return
    self._edit_katago_path_json("config", config_path)


  def _edit_katago_path_json(self, key: str, path: str):
    katago_path_json = load_json(KATAGO_VAR_PATH)
    if key not in katago_path_json:
      return
    katago_path_json[key] = path
    update_json(KATAGO_VAR_PATH, katago_path_json)
    self.main_window.update_katago_path()


  # Dialog Open
  def open_katago_setting_dialog(self):
    self.katago_setting_dialog.exec()


  def open_display_setting_dialog(self):
    self.display_setting_dialog.exec()


  def open_player_setting_dialog(self):
    self.player_setting_dialog.exec()


  # Update Setting
  def _set_katago_setting(self):
    self.main_window.update_katago_setting()


  def _set_display_setting(self):
    self.main_window.update_display_setting()


  def _set_player_setting(self, black: str, white: str):
    self.main_window.update_player_name(black, white)