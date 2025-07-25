import webbrowser
import os
import subprocess
import shutil

from pathlib import Path
from ..settings import PROJECT_PATH


def check_terminal():
    terminals = [
        'qterminal',
        'lxterminal',
        'xfce4-terminal',
        'gnome-terminal',
        'konsole',
        'xterm',
        'mate-terminal',
        'tilix'
    ]
    for terminal_name in terminals:
        terminal_path = shutil.which(terminal_name)
        if terminal_path:
            return terminal_name, terminal_path
    return None, None

terminal_name, terminal_path = check_terminal()

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
    subprocess.Popen(['xdg-open', file])
    os.chdir(PROJECT_PATH)


def locate_file(file):
    """定位文件
    """
    if terminal_name in (
        None, 'qterminal', 'lxterminal',
        'xfce4-terminal', 'xterm', 'tilix'
    ):
        return False, '当前系统不支持这个功能.'
    else:
        # to target system to debug
        return True, ''


def open_directory(directory):
    subprocess.Popen(['xdg-open', directory])


def open_console(directory):
    if not terminal_path:
        return
    subprocess.Popen(
        [terminal_path],
        cwd=directory,
        start_new_session=True
    )


def open_ftp(ftp_url):
    subprocess.Popen(['xdg-open', ftp_url])

def use_editor_open_path(editor, path):
    subprocess.Popen([editor, path])
