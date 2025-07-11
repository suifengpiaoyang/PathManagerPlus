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
    QFileDialog,
    QInputDialog,
    QDialog,
    QLineEdit,
    QLabel
)
from PySide2.QtCore import Qt, Signal
from .ui.main_window import Ui_MainWindow
from .ui.config_form import Ui_ConfigForm
from .ui.add_path_form import Ui_AddPathForm
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
    config = JsonDb(
        {
            "editor_path": None,
            "editor_name": None,
            "maximize_window_on_startup": False,
            "expand_tree_on_startup": False,
            "hide_toolbar": False
        }
    )
    config.to_json(CONFIG_FILE)


def load_qss():
    with open(STYLE_FILE, 'r', encoding='utf-8')as fl:
        qss = fl.read()
    return qss


class ConfigForm(QDialog):

    update_config = Signal(JsonDb)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_ConfigForm()
        self.ui.setupUi(self)
        self.setWindowFlags(
            Qt.Window |
            Qt.WindowMinimizeButtonHint |
            Qt.WindowMaximizeButtonHint |
            Qt.WindowCloseButtonHint
        )

        self.has_edited = False

        # set gui icon
        if os.path.exists(ICON_PATH):
            self.setWindowIcon(QIcon(ICON_PATH))

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
        if self.config.get('maximize_window_on_startup', False):
            self.ui.maximizeWindow.setChecked(True)
        if self.config.get('expand_tree_on_startup', False):
            self.ui.expandTree.setChecked(True)
        if self.config.get('hide_toolbar', False):
            self.ui.hideToolbar.setChecked(True)

        self.ui.pushButton.clicked.connect(self.choose_editor)
        self.ui.pushButtonConfirm.clicked.connect(self.confirm)
        self.ui.pushButtonCancel.clicked.connect(self.cancel)
        self.ui.maximizeWindow.toggled.connect(self.handle_maximize_window)
        self.ui.expandTree.toggled.connect(self.handle_expand_tree)
        self.ui.hideToolbar.toggled.connect(self.handle_hide_toolbar)

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

    def handle_expand_tree(self, checked):
        self.config['expand_tree_on_startup'] = checked
        self.has_edited = True

    def handle_maximize_window(self, checked):
        self.config['maximize_window_on_startup'] = checked
        self.has_edited = True

    def handle_hide_toolbar(self, checked):
        self.config['hide_toolbar'] = checked
        self.has_edited = True

    def cancel(self):
        del self.config
        self.has_edited = False
        self.close()

    def confirm(self):
        self.has_edited = False
        self.update_config.emit(self.config)
        self.close()


class AddPathForm(QDialog):

    path_data_submit = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_AddPathForm()
        self.ui.setupUi(self)
        self.setWindowFlags(
            Qt.Window |
            Qt.WindowMinimizeButtonHint |
            Qt.WindowMaximizeButtonHint |
            Qt.WindowCloseButtonHint
        )

        # set gui icon
        if os.path.exists(ADD_ICON_PATH):
            self.setWindowIcon(QIcon(ADD_ICON_PATH))

        # handle slots
        self.ui.pushButtonConfirm.clicked.connect(self.confirm)
        self.ui.pushButtonCancel.clicked.connect(self.cancel)
        self.ui.pushButtonAddMore.clicked.connect(self.add_more)

    def clear_all_widgets(self):
        self.ui.lineEditName.clear()
        self.ui.lineEditPath.clear()
        self.ui.plainTextEditComment.clear()
        self.ui.lineEditName.setFocus()

    def fetch_data(self):
        name = self.ui.lineEditName.text().strip()
        path = self.ui.lineEditPath.text().strip()
        comment = self.ui.plainTextEditComment.toPlainText().strip()
        payload = {
            'name': name,
            'path': path,
            'comment': comment
        }
        return payload

    def add_more(self):
        payload = self.fetch_data()
        self.path_data_submit.emit(payload)
        self.clear_all_widgets()

    def confirm(self):
        payload = self.fetch_data()
        self.path_data_submit.emit(payload)
        self.close()

    def cancel(self):
        self.close()


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.splitter.setSizes([200, 600])

        self.BASE_WINDOW_TITLE = self.windowTitle()
        self.has_edited = False

        # 添加 QLineEdit 到工具栏
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("搜索")
        self.search_box.setMaximumWidth(200)
        self.ui.toolBar.addSeparator()
        self.ui.toolBar.addWidget(self.search_box)
        self.search_box.returnPressed.connect(self.handle_search)

        # set gui icon
        if os.path.exists(ICON_PATH):
            self.setWindowIcon(QIcon(ICON_PATH))
        if os.path.exists(SAVE_ICON_PATH):
            self.ui.saveAction.setIcon(QIcon(SAVE_ICON_PATH))
        if os.path.exists(ADD_ICON_PATH):
            self.ui.addAction.setIcon(QIcon(ADD_ICON_PATH))
        if os.path.exists(DELETE_ICON_PATH):
            self.ui.deleteAction.setIcon(QIcon(DELETE_ICON_PATH))
        if os.path.exists(SETTINGS_ICON_PATH):
            self.ui.configAction.setIcon(QIcon(SETTINGS_ICON_PATH))

        # data init
        if not os.path.exists(DATABASE):
            self.data = gen_base_data()
            self.data.to_json(DATABASE)
        else:
            self.data = DataStorage.from_json(DATABASE)
            status = self.data.check_data_integrity()
            if not status:
                # 修复数据的同时，将修复完的数据保存到数据库。
                self.data.fix_data(DATABASE)
        self.build_tree()

        # 最大化窗口
        if config.get('maximize_window_on_startup', False):
            self.showMaximized()
        # 展开所有树节点
        if config.get('expand_tree_on_startup', False):
            self.ui.treeWidget.expandAll()
        if config.get('hide_toolbar', False):
            self.ui.toolBar.hide()

        # add right click menu
        self.add_context_menu()
        # 初始化右键弹出菜单
        self.init_listwidget_context_menu()
        self.init_treewidget_context_menu()

        # 设置状态栏内容
        node_count = self.data.node_count()
        # 左侧状态
        self.label_left = QLabel()
        self.ui.statusBar.addWidget(self.label_left)
        self.label_left.setFixedWidth(400)
        # 中间状态
        self.label_center = QLabel()
        self.ui.statusBar.addWidget(self.label_center)
        self.label_center.setFixedWidth(400)
        self.update_statusbar_left()

        # handle slots
        self.ui.saveAction.triggered.connect(self.save)
        self.ui.addAction.triggered.connect(self.show_add_path_form)
        self.ui.deleteAction.triggered.connect(self.delete_items)
        self.ui.treeWidget.itemClicked.connect(self.tree_item_click)
        self.ui.listWidget.dropMessage.connect(self.drop_add_item)
        self.ui.listWidget.clicked.connect(self.listwidget_left_click)
        self.ui.listWidget.itemDoubleClicked.connect(self.double_click_event)
        self.ui.configAction.triggered.connect(self.open_config_form)
        self.ui.lineEditName.editingFinished.connect(self.finish_edit)
        self.ui.textEditPath.editingFinished.connect(self.change_path_data)
        self.ui.textEditComment.editingFinished.connect(
            self.change_comment_data)
        self.ui.listWidget.dragDropSignal.connect(self.list_item_drop)
        self.ui.treeWidget.internalItemDropFinished.connect(
            self.internal_tree_item_drop)
        self.ui.treeWidget.externalFilesDroppedOnTreeItem.connect(
            self.drop_add_item)
        self.ui.treeWidget.updateListValue.connect(self.update_list_value)
        self.ui.treeWidget.listItemsDroppedOnTreeItem.connect(
            self.handle_list_drop)
        self.ui.listWidget.listKeyPressSignal.connect(self.list_key_press)
        self.ui.treeWidget.treeKeyPressSignal.connect(self.tree_key_press)
        self.ui.treeWidget.currentItemChanged.connect(self.tree_item_change)

        self.search_node = None
        self.search_box.setFocus()

    def update_statusbar_left(self):
        node_count = self.data.node_count() - 1
        item_count = self.data.item_count()
        self.label_left.setText(f'总共：{node_count}节点，{item_count}记录')

    def _format_data(self, data):
        return data if data is not None else ''

    def handle_search(self):
        text = self.search_box.text().strip()
        if len(text) == 0:
            return

        # ui 层面
        self.clear_input_widgets()
        self.ui.listWidget.clear()
        if self.search_node is None:
            self.search_node = QTreeWidgetItem(self.ui.treeWidget)
            self.search_node.setText(0, '搜索结果')
            self.ui.treeWidget.setCurrentItem(self.search_node)
        result_count = 0

        # 不区分大小写搜索 name, path, comment
        # 这里的部分后续如果要增强搜索功能，比如正则表达式之类的，
        # 需要在这里进行接口改变。
        text = text.lower()
        for item_id in self.data['items']:
            item_data = self.data['items'][item_id]
            name = self._format_data(item_data.get('name'))
            path = self._format_data(item_data.get('path'))
            comment = self._format_data(item_data.get('comment'))
            if text in name.lower() \
                or text in path.lower()\
                    or text in comment.lower():
                item = QListWidgetItem(name)
                item.setData(Qt.UserRole, item_id)
                self.ui.listWidget.addItem(item)
                result_count += 1
        # 更新状态栏
        self.label_center.setText(f'搜索结果：{result_count}')

    def init_listwidget_context_menu(self):
        self.action_open_selected_path = QAction('打开目标路径')
        self.action_open_console_window = QAction('打开console窗口')
        self.action_open_file_with_editor = QAction()
        self.action_open_path_with_editor = QAction()
        self.action_locate_file = QAction('定位文件')
        self.action_open_selected_file = QAction('打开目标文件(同双击)')
        self.action_delete_items = QAction('删除')

        self.action_open_selected_path.triggered.connect(
            self.open_selected_directories)
        self.action_open_console_window.triggered.connect(
            self.open_console_windows)
        self.action_open_file_with_editor.triggered.connect(
            lambda: self.open_with_editor(flag='file'))
        self.action_open_path_with_editor.triggered.connect(
            lambda: self.open_with_editor(flag='path'))
        self.action_locate_file.triggered.connect(self.locate_files)
        self.action_open_selected_file.triggered.connect(
            self.open_selected_files)
        self.action_delete_items.triggered.connect(self.delete_items)

        self.listwidget_menu = QMenu(self.ui.listWidget)
        self.listwidget_menu.addAction(self.action_locate_file)
        self.listwidget_menu.addAction(self.action_open_selected_path)
        self.listwidget_menu.addAction(self.action_open_console_window)
        self.listwidget_menu.addSeparator()
        self.listwidget_menu.addAction(self.action_open_file_with_editor)
        self.listwidget_menu.addAction(self.action_open_path_with_editor)
        self.listwidget_menu.addSeparator()
        self.listwidget_menu.addAction(self.action_delete_items)
        self.listwidget_menu.addAction(self.action_open_selected_file)

    def init_treewidget_context_menu(self):
        self.action_add_node = QAction('添加节点')
        self.action_add_sub_node = QAction('添加子节点')
        self.action_edit_node_name = QAction('修改节点名称')
        self.action_delete_node = QAction('删除节点')

        self.action_add_node.triggered.connect(self.add_node)
        self.action_add_sub_node.triggered.connect(self.add_sub_node)
        self.action_edit_node_name.triggered.connect(self.edit_node_name)
        self.action_delete_node.triggered.connect(self.delete_node)

        self.treewidget_menu = QMenu(self.ui.treeWidget)
        self.treewidget_menu.addAction(self.action_add_node)
        self.treewidget_menu.addAction(self.action_add_sub_node)
        self.treewidget_menu.addAction(self.action_edit_node_name)
        self.treewidget_menu.addSeparator()
        self.treewidget_menu.addAction(self.action_delete_node)

    def tree_item_change(self, current, previous):
        if current is None:
            return
        if self.search_node is not None and previous == self.search_node:
            index = self.ui.treeWidget.indexOfTopLevelItem(self.search_node)
            self.ui.treeWidget.takeTopLevelItem(index)
            self.search_node = None
            # 更新状态栏
            self.label_center.setText('')
        self.tree_item_click(current)

    def tree_key_press(self, key):
        if key == 'right':
            if self.ui.listWidget.count() > 0:
                self.ui.listWidget.setFocus()
                item = self.ui.listWidget.currentItem()
                self.ui.listWidget.setCurrentItem(item)
                self.listwidget_left_click(item)

    def list_key_press(self, key):
        if key in ('up', 'down'):
            item = self.ui.listWidget.currentItem()
            self.listwidget_left_click(item)
        elif key == 'left':
            self.ui.treeWidget.setFocus()
        elif key == 'enter':
            self.double_click_event()
        else:
            pass

    def show_add_path_form(self):
        # 不能够直接显示
        node = self.ui.treeWidget.currentItem()
        if not node:
            QMessageBox.about(
                self,
                '提示',
                '当前没有选中节点，你需要选中一个节点后才能使用该功能。'
            )
            return
        self.add_path_form = AddPathForm(self)
        self.add_path_form.path_data_submit.connect(
            self.handle_path_data_submit
        )
        self.add_path_form.show()

    def handle_path_data_submit(self, payload):
        node = self.ui.treeWidget.currentItem()
        if not node:
            return
        node_id = node.data(0, Qt.UserRole)
        item_id = self.data.add_item(payload, node_id)
        # 更新 listWidget 的 UI
        self.tree_item_click(node)
        row_count = self.ui.listWidget.count()
        last_item = self.ui.listWidget.item(row_count - 1)
        # last_item_id = last_item.data(Qt.UserRole)
        # last_item_data = self.data['items'][last_item_id]
        # print(last_item_data)
        self.ui.listWidget.setFocus()
        self.ui.listWidget.setCurrentItem(last_item)
        self.listwidget_left_click(last_item)
        self.set_has_edited(True)

    def handle_list_drop(self, payload):
        tree_node = payload['item']
        ids = payload['ids']
        if not tree_node or len(ids) == 0:
            return
        tree_node_id = tree_node.data(0, Qt.UserRole)
        # 在实际情况中，操作上不可能两个不同 parent_id 的
        # 进行一起拖动，所以如果是同一个树节点上进行将 listWidget
        # 的项拖动到原来节点，就作为无效操作。
        first_item_data = self.data['items'][ids[0]]
        if first_item_data['parent_id'] == tree_node_id:
            return
        for item_id in ids:
            list_item_data = self.data['items'][item_id]
            parent_id = list_item_data['parent_id']
            self.data.move_item_to_node(item_id, tree_node_id)
            # 这里还缺少 ui 处理逻辑
        self.tree_item_click(tree_node)
        self.set_has_edited(True)

    def update_list_value(self, node):
        self.tree_item_click(node, 0)

    def _get_parent_id(self, qt_node):
        """
        qt_node: type QTreeWidgetItem

        UI 层面第一层的节点的父节点是 None，而在数据层面，第一层的父节点
        是 root，而 root 的父节点才是 None
        所以，如果 UI 返回的父节点对象是 None 的话，就意味着它们是在第一层，
        对应的数据层面父节点的 id 应该是 root。而如果返回的父节点是一个实实在在
        的对象的话，那么，实际上父节点 id 也就是这个节点所存的那个值
        """
        if qt_node is None:
            parent_id = 'root'
        else:
            parent_id = qt_node.data(0, Qt.UserRole)
        return parent_id

    def internal_tree_item_drop(self, payload):

        # parse data
        node = payload['item']
        old_index = payload['old_index']
        new_index = payload['new_index']
        old_parent = payload['old_parent']
        new_parent = payload['new_parent']
        if not node:
            return
        # 移动一个节点需要知道四个要素：
        # 1. 原来节点的父节点的 id
        # 2. 原来节点在父节点中的位置，也就是下标
        # 3. 移动后节点的父节点的 id
        # 4. 移动后在父节点中的位置，也就是下标
        # 两个下标在 UI 层面一下就拿到了。所以需要着重处理的是父节点的问题。
        node_id = node.data(0, Qt.UserRole)
        new_parent_id = self._get_parent_id(new_parent)
        old_parent_id = self._get_parent_id(old_parent)
        # print(
        #     f'{self.data.get_node_name(old_parent_id)}>'
        #     f'{self.data.get_node_name(node_id)} >> '
        #     f'{self.data.get_node_name(new_parent_id)}>'
        #     f'{self.data.get_node_name(node_id)}'
        # )
        # print(f'{old_parent_id}>{node_id} >> {new_parent_id}>{node_id}')
        if old_parent_id == new_parent_id and old_index == new_index:
            return
        elif old_parent_id == new_parent_id and old_index != new_index:
            self.data.change_node_index(node_id, new_index)
        else:
            self.data.change_node_parent(node_id, new_parent_id, new_index)
        self.set_has_edited(True)

    def list_item_drop(self, payload):
        item = self.ui.listWidget.currentItem()
        if not item:
            return
        darg_item = payload['drag_item']
        start_row = payload['start_row']
        end_row = payload['end_row']
        item_id = item.data(Qt.UserRole)
        item_data = self.data['items'][item_id]
        parent_id = item_data['parent_id']

        # 处理 UI
        row = self.ui.listWidget.row(item)
        self.ui.listWidget.takeItem(start_row)
        self.ui.listWidget.insertItem(end_row, item)
        self.ui.listWidget.setCurrentRow(end_row)

        # 处理数据层面
        self.data.move_item_within_node(item_id, end_row)
        self.set_has_edited(True)

    def change_path_data(self):
        node = self.ui.treeWidget.currentItem()
        if not node:
            return
        item = self.ui.listWidget.currentItem()
        if not item:
            return
        item_id = item.data(Qt.UserRole)
        item_data = self.data['items'][item_id]
        path = self.ui.textEditPath.toPlainText()
        # 处理数据层
        self.data.update_item(item_id, {'path': path})
        self.set_has_edited(True)

    def change_comment_data(self):
        node = self.ui.treeWidget.currentItem()
        if not node:
            return
        item = self.ui.listWidget.currentItem()
        if not item:
            return
        item_id = item.data(Qt.UserRole)
        item_data = self.data['items'][item_id]
        comment = self.ui.textEditComment.toPlainText()
        # 处理数据层
        self.data.update_item(item_id, {'comment': comment})
        self.set_has_edited(True)

    def finish_edit(self):
        node = self.ui.treeWidget.currentItem()
        if not node:
            return
        item = self.ui.listWidget.currentItem()
        if not item:
            return
        item_id = item.data(Qt.UserRole)
        item_data = self.data['items'][item_id]
        name = self.ui.lineEditName.text()
        if name == item_data['name']:
            return
        # 处理数据层
        self.data.update_item(item_id, {'name': name})
        # 处理 UI 层
        item.setText(name)
        self.set_has_edited(True)

    def open_config_form(self):
        self.config_form = ConfigForm(self)
        self.config_form.update_config.connect(self.update_config)
        self.config_form.exec_()

    def update_config(self, payload):
        config.update(payload)
        config.to_json(CONFIG_FILE)
        # 这里可能后续还需要有修改字体后更新窗体渲染的代码
        # 支持部分配置功能实时更新
        if 'hide_toolbar' in payload:
            if payload['hide_toolbar']:
                self.ui.toolBar.hide()
            else:
                self.ui.toolBar.show()

    def add_context_menu(self):
        self.ui.listWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.listWidget.customContextMenuRequested.connect(
            self.show_context_menu)
        self.ui.treeWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.treeWidget.customContextMenuRequested.connect(
            self.show_tree_context_menu)

    def build_tree(self):
        self.ui.treeWidget.setHeaderHidden(True)
        # 渲染树节点的需要，渲染完后，这个实例变量就不需要了。
        # 感觉还是不维护的好。因为可以减少很多时间和精力，似乎也
        # 没有必要。想要获得的目标节点对象一般都很容易就获得了。
        self.tree_item_map = {}
        for node_id in self.data['nodes']['root']['sub_nodes']:
            self.render_node(node_id)
        # 用完直接删除掉，回收内存。
        del self.tree_item_map
        item_count = self.ui.treeWidget.topLevelItemCount()
        if item_count > 0:
            item = self.ui.treeWidget.topLevelItem(0)
            self.ui.treeWidget.setFocus()
            item.setSelected(True)
            item.setExpanded(True)
            # self.tree_item_click(item, 0)

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

    def tree_item_click(self, item, column=0):
        if item is None:
            return
        node_id = item.data(0, Qt.UserRole)
        if node_id is None:
            # 在搜索模式中
            return
        name = item.text(0)
        self.ui.listWidget.clear()
        self.clear_input_widgets()
        item_ids = self.data['nodes'][node_id]['items']
        for item_id in item_ids:
            item = self.data['items'][item_id]
            item = QListWidgetItem(item['name'])
            item.setData(Qt.UserRole, item_id)
            self.ui.listWidget.addItem(item)

    def listwidget_left_click(self, item=None):
        self.clear_input_widgets()
        if item is None:
            item = self.ui.listWidget.currentItem()
            if item is None:
                return
        item_data = self.get_listwidget_item_data(item)
        self.ui.lineEditName.setText(item_data['name'])
        self.ui.textEditPath.insertPlainText(item_data['path'])
        self.ui.textEditComment.insertPlainText(item_data['comment'])

    def double_click_event(self):
        self.open_selected_files()

    def get_listwidget_selected_items(self):
        items = self.ui.listWidget.selectedItems()
        if not items:
            return
        if len(items) > 5:
            QMessageBox.about(
                self,
                '提示',
                '当前最大允许同时进行任务数是5个！'
            )
            return
        return items

    def get_listwidget_item_data(self, item):
        item_id = item.data(Qt.UserRole)
        item_data = self.data['items'][item_id]
        return item_data

    def handle_open_file(self, path):
        """
        处理打开单个文件，附带 UI 反馈
        """
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

    def handle_directory(self, path, action_type):
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

    def handle_open_directory(self, path):
        return self.handle_directory(path, 'open_directory')

    def handle_open_console(self, path):
        return self.handle_directory(path, 'open_console')

    def open_selected_files(self):
        items = self.get_listwidget_selected_items()
        if not items:
            return
        for item in items:
            item_data = self.get_listwidget_item_data(item)
            path = item_data['path']
            self.handle_open_file(path)

    def open_selected_directories(self):
        items = self.get_listwidget_selected_items()
        if not items:
            return
        for item in items:
            item_data = self.get_listwidget_item_data(item)
            path = item_data['path']
            self.handle_open_directory(path)

    def open_console_windows(self):
        items = self.get_listwidget_selected_items()
        if not items:
            return
        for item in items:
            item_data = self.get_listwidget_item_data(item)
            path = item_data['path']
            self.handle_open_console(path)

    def handle_locate_file(self, path):
        if not path:
            return
        if not os.path.exists(path):
            QMessageBox.critical(self, '错误', f'找不到该文件：{path}')
            return
        system_actions.locate_file(path)

    def locate_files(self):
        items = self.get_listwidget_selected_items()
        if not items:
            return
        for item in items:
            item_data = self.get_listwidget_item_data(item)
            path = item_data['path']
            self.handle_locate_file(path)

    def delete_items(self):
        """输出列表控件的项
        """
        selected_items = self.ui.listWidget.selectedItems()
        if len(selected_items) == 0:
            QMessageBox.about(
                self,
                '提示',
                '此功能用于删除列表上的项。你需要先选中项才能使用该功能。'
            )
            return
        for item in selected_items:
            row = self.ui.listWidget.row(item)
            self.ui.listWidget.takeItem(row)    # 处理UI界面
            item_id = item.data(Qt.UserRole)
            self.data.remove_item(item_id)      # 处理数据删除
        count = self.ui.listWidget.count()
        if count > 0:
            current_item = self.ui.listWidget.currentItem()
            self.ui.listWidget.setCurrentItem(current_item)
            self.listwidget_left_click(current_item)
        elif count == 0:
            self.clear_input_widgets()
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
        self.action_open_file_with_editor.setText(
            f"使用 {editor_name} 打开文件")
        self.action_open_path_with_editor.setText(
            f"使用 {editor_name} 打开文件夹")
        self.listwidget_menu.exec_(
            self.ui.listWidget.mapToGlobal(position))

        # 右键点击时顺带触发了一次左键选中更新信息。
        self.listwidget_left_click()

    def show_tree_context_menu(self, position):
        # item = self.ui.treeWidget.currentItem()
        # self.tree_item_click(item, 0)
        self.treewidget_menu.exec_(
            self.ui.treeWidget.mapToGlobal(position))

    def add_node(self):
        name, ok = QInputDialog.getText(
            self, "请输入节点名称", "节点名称："
        )
        if not ok:
            return

        # 数据层面处理
        node = self.ui.treeWidget.currentItem()
        # 当所有节点都删除时，当前项将会变成 None
        if node is None:
            parent_id = 'root'
        else:
            hover_node_id = node.data(0, Qt.UserRole)
            hover_node = self.data['nodes'][hover_node_id]
            parent_id = hover_node['parent_id']
        # 调用 api 添加数据
        new_node_id = self.data.add_node(name, parent_id)

        # UI 层面处理
        if parent_id == 'root':
            item = QTreeWidgetItem(self.ui.treeWidget)
        else:
            item = QTreeWidgetItem(node.parent())
        item.setText(0, name)
        item.setData(0, Qt.UserRole, new_node_id)
        self.ui.treeWidget.setFocus()
        self.ui.treeWidget.setCurrentItem(item)
        # self.tree_item_click(item)
        self.set_has_edited(True)
        self.update_statusbar_left()

    def add_sub_node(self):
        name, ok = QInputDialog.getText(
            self, "请输入子节点名称", "子节点名称："
        )
        if not ok:
            return

        # 数据层面处理
        node = self.ui.treeWidget.currentItem()
        hover_node_id = node.data(0, Qt.UserRole)
        parent_id = hover_node_id
        new_node_id = self.data.add_node(name, parent_id)

        # UI 层面处理
        item = QTreeWidgetItem(node)
        item.setText(0, name)
        item.setData(0, Qt.UserRole, new_node_id)
        self.ui.treeWidget.setFocus()
        self.ui.treeWidget.setCurrentItem(item)
        # self.tree_item_click(item)
        self.set_has_edited(True)
        self.update_statusbar_left()

    def edit_node_name(self):
        node = self.ui.treeWidget.currentItem()
        node_id = node.data(0, Qt.UserRole)
        node_data = self.data['nodes'][node_id]
        name = node_data['name']

        name, ok = QInputDialog.getText(
            self,
            "修改节点名称",
            "节点名称：",
            text=name
        )
        if not ok:
            return
        self.data.change_node_name(node_id, name)
        node.setText(0, name)
        self.set_has_edited(True)

    def delete_node(self):
        flag = QMessageBox.question(
            self,
            '警告',
            '你确定要删除该节点和所有字节点，以及全部相关的数据？',
            QMessageBox.Yes | QMessageBox.Cancel
        )
        if flag != QMessageBox.StandardButton.Yes:
            return
        node = self.ui.treeWidget.currentItem()
        node_id = node.data(0, Qt.UserRole)

        # 处理数据层面
        self.data.remove_node(node_id)

        # 处理 UI 层面
        parent = node.parent()
        if parent:
            parent.removeChild(node)  # 从父节点中移除
        else:
            index = self.ui.treeWidget.indexOfTopLevelItem(node)
            self.ui.treeWidget.takeTopLevelItem(index)  # 删除顶层节点
        # 如果还有节点，则刷新列表项
        node = self.ui.treeWidget.currentItem()
        if not node:
            self.ui.listWidget.clear()
        # else:
        #     self.tree_item_click(node)
        self.set_has_edited(True)
        self.update_statusbar_left()

    def open_with_editor(self, flag):
        items = self.get_listwidget_selected_items()
        if not items:
            return
        for item in items:
            item_data = self.get_listwidget_item_data(item)
            path = item_data['path']
            self.handle_open_with_editor(path, flag)

    def handle_open_with_editor(self, path, flag):
        if flag not in ('file', 'path'):
            print('flag 必须为 file 或者 path')
            return
        editor_path = config.get('editor_path', None)
        if editor_path is None:
            QMessageBox.about(
                self,
                '提示',
                '请先在[选项>配置]里面配置代码编辑器路径。'
            )
            return
        if not os.path.exists(editor_path):
            QMessageBox.critical(self, '错误', f'[{editor_path}]不存在！')
            return
        if not path:
            return
        if not os.path.exists(path):
            QMessageBox.critical(self, '错误', f'找不到[{path}]！')
            return
        if flag == 'file':
            if os.path.isdir(path):
                QMessageBox.critical(
                    self,
                    '错误',
                    f'无法通过打开文件的方式打开文件夹！[{path}]'
                )
                return
            target = path
        elif flag == 'path':
            if os.path.isdir(path):
                target = path
            else:
                target = os.path.dirname(path)
        else:
            raise TypeError
        subprocess.Popen([editor_path, target])

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
        self.listwidget_left_click(item)
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
            flag = QMessageBox.question(
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
    app.setStyleSheet(load_qss())
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
