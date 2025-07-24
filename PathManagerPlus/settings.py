import os


PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))
STATIC_PATH = os.path.join(PROJECT_PATH, 'static')
DATABASE = os.path.join(PROJECT_PATH, 'data.json')
CONFIG_FILE = os.path.join(PROJECT_PATH, 'config.json')
ICON_PATH = os.path.join(STATIC_PATH, 'icons')
QSS_PATH = os.path.join(STATIC_PATH, 'qss')

# ICON settings
PROJECT_ICON_PATH = os.path.join(ICON_PATH, 'folder.ico')
SAVE_ICON_PATH = os.path.join(ICON_PATH, 'save.ico')
ADD_ICON_PATH = os.path.join(ICON_PATH, 'add.ico')
DELETE_ICON_PATH = os.path.join(ICON_PATH, 'delete.ico')
SETTINGS_ICON_PATH = os.path.join(ICON_PATH, 'settings.ico')

# qss
WINDOWS_QSS_PATH = os.path.join(QSS_PATH, 'windows.qss')
LINUX_QSS_PATH = os.path.join(QSS_PATH, 'linux.qss')
MAC_QSS_PATH = os.path.join(QSS_PATH, 'mac.qss')
