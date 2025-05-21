import os


DATABASE = 'data.json'
PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))
STATIC_PATH = os.path.join(PROJECT_PATH, 'static')
DATABASE = os.path.join(PROJECT_PATH, DATABASE)
