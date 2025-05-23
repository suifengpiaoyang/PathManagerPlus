import os
import sys
import webbrowser
import subprocess
import platform

from PySide2.QtGui import (
    QIcon,
    QKeySequence
)
from PySide2.QtWidgets import (
    QApplication,
    QMainWindow,
    QTreeWidgetItem,
    QListWidgetItem,
    QMessageBox,
    QShortcut,
    QAction,
    QMenu
)
from PySide2.QtCore import Qt
from .ui.main_window import Ui_MainWindow
from .settings import *
from .handle_data import (
    gen_base_data,
    DataStorage,
    get_data_format
)


system = platform.system()

if system == "Windows":
    from .actions import windows_actions as system_actions
elif system == "Linux":
    from .actions import linux_actions as system_actions
elif system == "Darwin":
    raise SysteExit('当前该程序的代码不支持这个系统。')


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.BASE_WINDOW_TITLE = self.windowTitle()
        self.has_edited = False

        # set gui icon
        icon_path = os.path.join(STATIC_PATH, 'folder.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # data init
        if not os.path.exists(DATABASE):
            self.data = gen_base_data()
            self.data.to_json(DATABASE)
        else:
            self.data = DataStorage.from_json(DATABASE)
        self.build_tree()

        # shortcuts
        shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        shortcut.activated.connect(self.save)

        # add right click menu
        self.add_context_menu()

        # handle slots
        self.ui.treeWidget.itemClicked.connect(self.tree_item_click)
        self.ui.listWidget.dropMessage.connect(self.drop_add_item)
        self.ui.listWidget.clicked.connect(self.left_click_event)
        self.ui.listWidget.itemDoubleClicked.connect(self.double_click_event)

    def add_context_menu(self):
        self.ui.listWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.listWidget.customContextMenuRequested.connect(
            self.show_context_menu)

    def build_tree(self):
        self.ui.treeWidget.setHeaderHidden(True)
        self.item_map = {}
        for node_id in self.data['nodes']['root']['sub_nodes']:
            self.render_node(node_id)
        item_count = self.ui.treeWidget.topLevelItemCount()
        if item_count > 0:
            item = self.ui.treeWidget.topLevelItem(0)
            self.ui.treeWidget.setFocus()
            item.setSelected(True)
            item.setExpanded(True)
            self.tree_item_click(item, 0)

    def render_node(self, node_id):
        node = self.data['nodes'][node_id]
        name = node['name']
        parent_id = node['parent_id']
        if parent_id == 'root':
            item = QTreeWidgetItem(self.ui.treeWidget)
        else:
            item = QTreeWidgetItem(self.item_map[parent_id])
        item.setText(0, name)
        item.setData(0, Qt.UserRole, node_id)
        self.item_map[node_id] = item
        for _node_id in self.data['nodes'][node_id]['sub_nodes']:
            self.render_node(_node_id)

    def tree_item_click(self, item, column):
        node_id = item.data(0, Qt.UserRole)
        name = item.text(0)
        self.ui.listWidget.clear()
        self.clear_input_widgets()
        item_ids = self.data['nodes'][node_id]['items']
        for item_id in item_ids:
            item = self.data['items'][item_id]
            item = QListWidgetItem(item['name'])
            item.setData(Qt.UserRole, item_id)
            self.ui.listWidget.addItem(item)

    def _left_click_event(self, item=None):
        self.clear_input_widgets()
        if item is None:
            item = self.ui.listWidget.currentItem()
        item_id = item.data(Qt.UserRole)
        item_data = self.data['items'][item_id]
        self.ui.lineEditName.setText(item_data['name'])
        self.ui.textEditPath.insertPlainText(item_data['path'])
        self.ui.textEditComment.insertPlainText(item_data['comment'])

    def left_click_event(self):
        self._left_click_event()

    def double_click_event(self):
        self.open_selected_file()

    def get_selected_path(self):
        item = self.ui.listWidget.currentItem()
        item_id = item.data(Qt.UserRole)
        item_data = self.data['items'][item_id]
        path = item_data['path']
        return path

    def open_selected_file(self):
        path = self.get_selected_path()
        if not path:
            return
        if path.startswith('http'):
            system_actions.open_url(path)
        elif path.startswith(('ftp', r'\\')):
            system_actions.open_ftp(path)
        elif os.path.exists(path):
            system_actions.open_file(path)
        else:
            QMessageBox.critical(self, '错误', f'找不到目标路径：{path}')

    def handle_selected_directory(self, action_type):
        path = self.get_selected_path()
        if not path:
            return
        if os.path.isdir(path):
            directory = path
        else:
            if not os.path.exists(path):
                QMessageBox.critical(self, '错误', f'找不到该文件：{path}')
                return
            directory = os.path.dirname(path)
        if directory and os.path.exists(directory):
            if action_type == 'open_directory':
                system_actions.open_directory(directory)
            elif action_type == 'open_console':
                system_actions.open_console(directory)
            else:
                raise TypeError
        else:
            QMessageBox.critical(self, '错误', f'找不到目标路径：{path}')

    def open_selected_directory(self):
        self.handle_selected_directory('open_directory')

    def open_console_window(self):
        self.handle_selected_directory('open_console')

    def locate_file(self):
        path = self.get_selected_path()
        if not path:
            return
        if not os.path.exists(path):
            QMessageBox.critical(self, '错误', f'找不到该文件：{path}')
            return
        system_actions.locate_file(path)

    def clear_input_widgets(self):
        """Clear all input widgets.
        """
        self.ui.lineEditName.clear()
        self.ui.textEditPath.clear()
        self.ui.textEditComment.clear()

    def show_context_menu(self, position):
        """Show context menu and handle slots.
        """
        # 右键点击时顺带触发了一次左键选中更新信息。
        self.left_click_event()
        open_selected_path = QAction('打开目标路径')
        open_console_window = QAction('打开console窗口')
        # open_file_with_sublime = QAction('使用sublime text打开文件')
        # open_path_with_sublime = QAction('使用sublime text打开文件夹')
        locate_file = QAction('定位文件')
        open_selected_file = QAction('打开目标文件(同双击)')

        open_selected_path.triggered.connect(self.open_selected_directory)
        open_console_window.triggered.connect(self.open_console_window)
        # open_file_with_sublime.triggered.connect(
        #     lambda: self.open_with_sublime(flag='file'))
        # open_path_with_sublime.triggered.connect(
        #     lambda: self.open_with_sublime(flag='path'))
        locate_file.triggered.connect(self.locate_file)
        open_selected_file.triggered.connect(self.open_selected_file)

        menu = QMenu(self.ui.listWidget)
        menu.addAction(locate_file)
        menu.addAction(open_selected_path)
        menu.addAction(open_console_window)
        menu.addSeparator()
        # menu.addAction(open_file_with_sublime)
        # menu.addAction(open_path_with_sublime)
        # menu.addSeparator()
        menu.addAction(open_selected_file)
        menu.exec_(self.ui.listWidget.mapToGlobal(position))

    def drop_add_item(self, urllist):
        node = self.ui.treeWidget.currentItem()
        node_id = node.data(0, Qt.UserRole)
        for QUrl in urllist:
            path = QUrl.toLocalFile()
            row_count = self.ui.listWidget.count()
            basename = os.path.basename(path)
            item_data = get_data_format('item')
            item_data['name'] = basename
            item_data['path'] = path
            item_id = self.data.add_item(item_data, node_id)
            item = QListWidgetItem(basename)
            item.setData(Qt.UserRole, item_id)
            self.ui.listWidget.addItem(item)
        self._left_click_event(item)
        item.setSelected(True)
        self.ui.listWidget.setCurrentItem(item)
        self.ui.listWidget.setFocus(Qt.OtherFocusReason)
        self.window().activateWindow()
        self.set_has_edited()

    def set_has_edited(self, state=True):
        self.has_edited = state
        if state:
            self.setWindowTitle(self.BASE_WINDOW_TITLE + ' *')
        else:
            self.setWindowTitle(self.BASE_WINDOW_TITLE)

    def save(self):
        self.data.to_json(DATABASE)
        self.set_has_edited(False)

    def closeEvent(self, event):
        # 保存最后关闭时窗口的大小
        # self.config['width'] = self.width()
        # self.config['height'] = self.height()
        # self.config.save(CONFIG_FILE)

        if self.has_edited:
            flag = QMessageBox.warning(
                self,
                '警告',
                '当前数据善未保存，是否要保存数据？',
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            if flag == QMessageBox.StandardButton.Yes:
                # 保存关闭
                self.save()
                event.accept()
            elif flag == QMessageBox.StandardButton.No:
                # 不保存数据，强制关闭
                event.accept()
            elif flag == QMessageBox.StandardButton.Cancel:
                # 取消关闭操作
                event.ignore()
        else:
            event.accept()


def main():

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
