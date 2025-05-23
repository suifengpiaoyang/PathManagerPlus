import webbrowser
import os
import subprocess
from pathlib import Path


def open_url(url):
    return webbrowser.open(url)


def open_file(file):
    os.startfile(file)


def locate_file(file):
    """定位文件
    Windows 平台对路径的要求很严格，需要用反斜杠，否则无法定位。
    """
    file = Path(file)
    subprocess.run(['explorer', '/select,', str(file.resolve())])


def open_directory(directory):
    os.startfile(directory)


def open_console(directory):
    os.system(f'start /D "{directory}"')


def open_ftp(ftp_url):
    subprocess.Popen(['explorer.exe', ftp_url])
