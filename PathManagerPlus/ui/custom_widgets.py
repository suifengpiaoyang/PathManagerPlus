from PySide2.QtCore import Signal, Qt
from PySide2.QtWidgets import (
    QListWidget,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QAbstractItemView
)


class CustomQListWidget(QListWidget):

    dropMessage = Signal(list)
    dragDropSignal = Signal(int, int)

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
            urls = event.mimeData().urls()
            self.dropMessage.emit(urls)
        elif event.mimeData().hasFormat(
                'application/x-qabstractitemmodeldatalist'):
            drop_position = event.pos()
            drop_row = self.row(self.itemAt(drop_position))
            start_row = self.currentRow()
            self.dragDropSignal.emit(start_row, drop_row)
            # event.accept()
        else:
            event.ignore()


class CustomQTreeWidget(QTreeWidget):
    dropMessage = Signal(list)
    dropFinished = Signal(dict)
    updateListValue = Signal(QTreeWidgetItem)

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
        # elif event.mimeData().hasFormat(
        #         "application/x-qabstractitemmodeldatalist"):
        #     event.accept()
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
            drag_data = {
                'item': item,
                'old_index': old_index,
                'new_index': new_index,
                'old_parent': old_parent,
                'new_parent': new_parent
            }
            self.dropFinished.emit(drag_data)
            self.updateListValue.emit(item)

    def handleFileDrop(self, event):
        item = self.currentItem()
        if not item:
            event.ignore()
            return
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            self.dropMessage.emit(urls)
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.source() == self:
            # 树控件内部拖拽。
            self.handleInternalDropEvent(event)
        elif isinstance(event.source(), CustomQListWidget):
            # 列表控件的项拖拽到树控件上
            pass
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
