import os
import sys
import webbrowser
import subprocess
import platform

from PySide2.QtGui import (
    QIcon,
    QKeySequence,
    QFont
)
from PySide2.QtWidgets import (
    QApplication,
    QMainWindow,
    QTreeWidgetItem,
    QListWidgetItem,
    QMessageBox,
    QShortcut,
    QAction,
    QMenu,
    QWidget,
    QFileDialog
)
from PySide2.QtCore import Qt, Signal
from .ui.main_window import Ui_MainWindow
from .ui.config_form import Ui_ConfigForm
from .settings import *
from .handle_data import (
    gen_base_data,
    DataStorage,
    get_data_format,
    JsonDb
)


system = platform.system()

if system == "Windows":
    from .actions import windows_actions as system_actions
elif system == "Linux":
    from .actions import linux_actions as system_actions
elif system == "Darwin":
    raise SysteExit('当前该程序的代码不支持这个系统。')

if os.path.exists(CONFIG_FILE):
    config = JsonDb.from_json(CONFIG_FILE)
else:
    config = JsonDb({})
    # 这里要不要保存是一个问题


class ConfigForm(QWidget):

    update_config = Signal(JsonDb)

    def __init__(self):
        super().__init__()
        self.ui = Ui_ConfigForm()
        self.ui.setupUi(self)

        self.has_edited = False

        # set gui icon
        icon_path = os.path.join(STATIC_PATH, 'folder.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # load config file
        if os.path.exists(CONFIG_FILE):
            self.config = JsonDb.from_json(CONFIG_FILE)
        else:
            self.config = JsonDb({})
        editor_path = self.config.get('editor_path')
        if editor_path:
            self.ui.lineEditEditorPath.setText(editor_path)
        editor_name = self.config.get('editor_name')
        if editor_name:
            self.ui.lineEditEditorName.setText(editor_name)

        self.ui.pushButton.clicked.connect(self.choose_editor)
        self.ui.pushButtonConfirm.clicked.connect(self.confirm)
        self.ui.pushButtonCancel.clicked.connect(self.cancel)

    def choose_editor(self):
        if system == 'Windows':
            path, _ = QFileDialog.getOpenFileName(
                self,
                '选择编辑器',
                None,
                'Program (*.exe)'
            )
            if not path:
                return
            self.ui.lineEditEditorPath.setText(path)
            name = os.path.basename(path)
            name = name.split('.')[0].title().replace('_', ' ')
            self.ui.lineEditEditorName.setText(name)
            self.config['editor_path'] = path
            self.config['editor_name'] = name
            self.has_edited = True

    def cancel(self):
        del self.config
        self.has_edited = False
        self.close()

    def confirm(self):
        self.has_edited = False
        self.update_config.emit(self.config)
        self.close()


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

        shortcut = QShortcut(QKeySequence("Delete"), self)
        shortcut.activated.connect(self.delete_item)

        # add right click menu
        self.add_context_menu()

        # handle slots
        self.ui.treeWidget.itemClicked.connect(self.tree_item_click)
        self.ui.listWidget.dropMessage.connect(self.drop_add_item)
        self.ui.listWidget.clicked.connect(self.left_click_event)
        self.ui.listWidget.itemDoubleClicked.connect(self.double_click_event)
        self.ui.configAction.triggered.connect(self.open_config_form)

    def open_config_form(self):
        self.config_form = ConfigForm()
        self.config_form.update_config.connect(self.update_config)
        self.config_form.show()

    def update_config(self, _config):
        config.update(_config)
        config.to_json(CONFIG_FILE)
        # 这里可能后续还需要有修改字体后更新窗体渲染的代码

    def add_context_menu(self):
        self.ui.listWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.listWidget.customContextMenuRequested.connect(
            self.show_context_menu)
        self.ui.treeWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.treeWidget.customContextMenuRequested.connect(
            self.show_tree_context_menu)

    def build_tree(self):
        self.ui.treeWidget.setHeaderHidden(True)
        # 太久了，有点忘记当初设定这个的原因了。
        self.tree_item_map = {}
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
            item = QTreeWidgetItem(self.tree_item_map[parent_id])
        item.setText(0, name)
        item.setData(0, Qt.UserRole, node_id)
        self.tree_item_map[node_id] = item
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

    def left_click_event(self, item=None):
        self.clear_input_widgets()
        if item is None:
            item = self.ui.listWidget.currentItem()
            if item is None:
                return
        item_id = item.data(Qt.UserRole)
        item_data = self.data['items'][item_id]
        self.ui.lineEditName.setText(item_data['name'])
        self.ui.textEditPath.insertPlainText(item_data['path'])
        self.ui.textEditComment.insertPlainText(item_data['comment'])

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

    def delete_item(self):
        """输出列表控件的项

        当前版本只支持删除一项。
        """
        current_row = self.ui.listWidget.currentRow()
        item = self.ui.listWidget.takeItem(current_row)  # 处理UI界面
        item_id = item.data(Qt.UserRole)
        self.data.remove_item(item_id)                   # 处理数据删除
        self.left_click_event()
        self.set_has_edited(True)

    def clear_input_widgets(self):
        """Clear all input widgets.
        """
        self.ui.lineEditName.clear()
        self.ui.textEditPath.clear()
        self.ui.textEditComment.clear()

    def show_context_menu(self, position):
        """Show context menu and handle slots.
        """
        current_row = self.ui.listWidget.currentRow()
        if current_row == -1:
            return

        editor_name = config.get('editor_name', '代码编辑器')
        editor_path = config.get('editor_path')

        # 右键点击时顺带触发了一次左键选中更新信息。
        self.left_click_event()
        open_selected_path = QAction('打开目标路径')
        open_console_window = QAction('打开console窗口')
        open_file_with_editor = QAction(f'使用{editor_name}打开文件')
        open_path_with_editor = QAction(f'使用{editor_name}打开文件夹')
        locate_file = QAction('定位文件')
        open_selected_file = QAction('打开目标文件(同双击)')
        delete_item = QAction('删除')

        open_selected_path.triggered.connect(self.open_selected_directory)
        open_console_window.triggered.connect(self.open_console_window)
        open_file_with_editor.triggered.connect(
            lambda: self.open_with_editor(flag='file'))
        open_path_with_editor.triggered.connect(
            lambda: self.open_with_editor(flag='path'))
        locate_file.triggered.connect(self.locate_file)
        open_selected_file.triggered.connect(self.open_selected_file)
        delete_item.triggered.connect(self.delete_item)

        menu = QMenu(self.ui.listWidget)
        menu.addAction(locate_file)
        menu.addAction(open_selected_path)
        menu.addAction(open_console_window)
        menu.addSeparator()
        menu.addAction(open_file_with_editor)
        menu.addAction(open_path_with_editor)
        menu.addSeparator()
        menu.addAction(delete_item)
        menu.addAction(open_selected_file)
        menu.exec_(self.ui.listWidget.mapToGlobal(position))

    def show_tree_context_menu(self, position):
        test_action = QAction('Test Action')

        test_action.triggered.connect(self.test_action)

        menu = QMenu(self.ui.treeWidget)
        menu.addAction(test_action)
        menu.exec_(self.ui.treeWidget.mapToGlobal(position))

    def test_action(self):
        print('This is a test.')

    def open_with_editor(self, flag):
        if flag not in ('file', 'path'):
            print('flag 必须为 file 或者 path')
            return
        editor_path = config.get('editor_path', None)
        if editor_path is None:
            QMessageBox.about(
                self,
                '提示',
                '请先在[首选项]里面配置代码编辑器路径。'
            )
            return
        if not os.path.exists(editor_path):
            QMessageBox.critical(self, '错误', f'[{editor_path}]不存在！')
            return
        item = self.ui.listWidget.currentItem()
        if item is None:
            return
        item_id = item.data(Qt.UserRole)
        item_data = self.data['items'][item_id]
        path = item_data['path']
        if not path:
            QMessageBox.critical(self, '错误', '路径不能为空值！')
            return
        if not os.path.exists(path):
            QMessageBox.critical(self, '错误', f'找不到[{path}]！')
            return
        if flag == 'file' and os.path.isdir(path):
            QMessageBox.critical(self, '错误', '目标是一个文件夹！')
            return
        subprocess.Popen([editor_path, path])

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
        self.left_click_event(item)
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
    font = QFont()
    font.setPointSize(13)  # 设置字体大小
    app.setFont(font)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
