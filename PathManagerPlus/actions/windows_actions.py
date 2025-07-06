import webbrowser
import os
import subprocess
from pathlib import Path
from ..settings import PROJECT_PATH


def open_url(url):
    return webbrowser.open(url)


def open_file(file):
    """
    切换到文件所在路径下去执行程序。
    因为有的程序读取配置文件或者数据时，不是以绝对路径读取的，
    而是直接读取一个文件名。这样默认的话，是需要在文件所在路径
    去执行程序的，否则就会出现路径错误。感觉这有点难以说明到底
    是程序的读取方式不严谨还是当前这个软件就得适配这种情形。
    """
    path = os.path.dirname(file)
    os.chdir(path)
    os.startfile(file)
    os.chdir(PROJECT_PATH)


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
