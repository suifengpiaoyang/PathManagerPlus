from PySide2.QtCore import (
    Signal,
    QDataStream,
    QByteArray,
    QIODevice,
    Qt
)
from PySide2.QtWidgets import (
    QListWidget,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QAbstractItemView
)


def getItemIdsFromEvent(event):
    ids = []
    fmt = "application/x-qabstractitemmodeldatalist"
    if not event.mimeData().hasFormat(fmt):
        return ids
    data = event.mimeData().data(fmt)
    stream = QDataStream(data, QIODevice.ReadOnly)

    while not stream.atEnd():
        row = stream.readInt32()
        col = stream.readInt32()
        map_items = stream.readInt32()
        for _ in range(map_items):
            role = stream.readInt32()
            value = stream.readQVariant()
            if role == Qt.UserRole:
                ids.append(str(value))
    return ids


class CustomQListWidget(QListWidget):

    dropMessage = Signal(list)
    dragDropSignal = Signal(dict)
    listKeyPressSignal = Signal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptDrops(True)

    def mimeTypes(self):
        mimetypes = super().mimeTypes()
        mimetypes.append('text/uri-list')
        return mimetypes

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        elif event.mimeData().hasFormat(
                'application/x-qabstractitemmodeldatalist'):
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            # 处理外面拖进来的文件，文件夹路径
            urls = event.mimeData().urls()
            self.dropMessage.emit(urls)
        elif event.mimeData().hasFormat(
                'application/x-qabstractitemmodeldatalist'):
            # 处理内部项的拖动，这里需要区分是树项内拖动还是项外拖动
            item = self.currentItem()
            if not item:
                event.ignore()
                return
            start_row = self.currentRow()
            drop_position = event.pos()
            end_row = self.row(self.itemAt(drop_position))
            payload = {
                'drag_item': item,
                'start_row': start_row,
                'end_row': end_row
            }
            self.dragDropSignal.emit(payload)
        else:
            event.ignore()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Up:
            self.listKeyPressSignal.emit('up')
        elif event.key() == Qt.Key_Down:
            self.listKeyPressSignal.emit('down')
        elif event.key() == Qt.Key_Left:
            self.listKeyPressSignal.emit('left')
        super().keyPressEvent(event)


class CustomQTreeWidget(QTreeWidget):
    externalFilesDroppedOnTreeItem = Signal(list)
    internalItemDropFinished = Signal(dict)
    updateListValue = Signal(QTreeWidgetItem)
    listItemsDroppedOnTreeItem = Signal(dict)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptDrops(True)

    def mimeTypes(self):
        mimetypes = super().mimeTypes()
        mimetypes.append('text/uri-list')
        return mimetypes

    def startDrag(self, supportedActions):
        # 拿到当前项
        item = self.currentItem()
        if item:
            self.updateListValue.emit(item)
        super().startDrag(supportedActions)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        elif event.mimeData().hasFormat(
                "application/x-qabstractitemmodeldatalist"):
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.source() == self:
            # 树控件的内部拖拽，使用默认的行为处理模式，保留
            # 拖动时的方框和一些比较人性化的行为。
            super().dragMoveEvent(event)
        elif isinstance(event.source(), CustomQListWidget):
            event.acceptProposedAction()
            item = self.itemAt(event.pos())
            if item:
                self.setCurrentItem(item)
                # 或者高亮选中
                item.setSelected(True)
                # 还需要打开树父节点
                if item.childCount() > 0 and not item.isExpanded():
                    item.setExpanded(True)
                # 这里还需要界面更新数据
                self.updateListValue.emit(item)
        elif event.mimeData().hasUrls():
            # 外部拖动文件文件夹进来时的行为
            event.acceptProposedAction()
            item = self.itemAt(event.pos())
            if item:
                self.setCurrentItem(item)
                # 或者高亮选中
                item.setSelected(True)
                # 还需要打开树父节点
                if item.childCount() > 0 and not item.isExpanded():
                    item.setExpanded(True)
                # 这里还需要界面更新数据
                self.updateListValue.emit(item)
        else:
            event.ignore()

    def handleInternalDropEvent(self, event):
        item = self.currentItem()
        if not item:
            event.ignore()
            return
        old_parent = item.parent()
        if old_parent is None:
            old_index = self.indexOfTopLevelItem(item)
        else:
            old_index = old_parent.indexOfChild(item)
        self.updateListValue.emit(item)
        super().dropEvent(event)
        self.currentItem().setSelected(False)
        new_parent = item.parent()
        if new_parent is None:
            new_index = self.indexOfTopLevelItem(item)
        else:
            new_index = new_parent.indexOfChild(item)
            new_parent.setExpanded(True)
        item.setSelected(True)
        if old_parent == new_parent and old_index == new_index:
            return
        else:
            payload = {
                'item': item,
                'old_index': old_index,
                'new_index': new_index,
                'old_parent': old_parent,
                'new_parent': new_parent
            }
            self.internalItemDropFinished.emit(payload)
            self.updateListValue.emit(item)

    def handleListItemToTree(self, event):
        """
        ids 为拖动到树控件上的 listWidget 的项对应 user_role 里面
        自己数据库设定的携带的 id 值。也就是对应的 uuid，不是 python
        系统中传统意义上对象的 id 值。
        """
        ids = getItemIdsFromEvent(event)
        if len(ids) == 0:
            return
        item = self.currentItem()
        if not item:
            return
        payload = {
            'item': item,
            'ids': ids
        }
        self.listItemsDroppedOnTreeItem.emit(payload)

    def handleFileDrop(self, event):
        item = self.currentItem()
        if not item:
            event.ignore()
            return
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            self.externalFilesDroppedOnTreeItem.emit(urls)
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.source() == self:
            # 树控件内部拖拽。
            self.handleInternalDropEvent(event)
        elif isinstance(event.source(), CustomQListWidget):
            # 列表控件的项拖拽到树控件上
            self.handleListItemToTree(event)
        elif event.mimeData().hasUrls():
            # 文件和文件夹等拖拽到树控件上。处理方式基本和拖拽到列表
            # 控件上相同。
            self.handleFileDrop(event)


class CustomQTextEdit(QTextEdit):

    editingFinished = Signal()

    def focusInEvent(self, event):
        self._base_data = self.toPlainText()
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        if self.toPlainText() != self._base_data:
            self.editingFinished.emit()
        super().focusOutEvent(event)
