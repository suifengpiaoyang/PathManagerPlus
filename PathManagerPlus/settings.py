import os


PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))
STATIC_PATH = os.path.join(PROJECT_PATH, 'static')
DATABASE = os.path.join(PROJECT_PATH, 'data.json')
CONFIG_FILE = os.path.join(PROJECT_PATH, 'config.json')
ICON_PATH = os.path.join(STATIC_PATH, 'folder.ico')
SAVE_ICON_PATH = os.path.join(STATIC_PATH, 'save.ico')
ADD_ICON_PATH = os.path.join(STATIC_PATH, 'add.ico')
DELETE_ICON_PATH = os.path.join(STATIC_PATH, 'delete.ico')
