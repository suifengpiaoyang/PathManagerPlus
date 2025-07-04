from PySide2.QtCore import Signal
from PySide2.QtWidgets import (
    QListWidget,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem
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
    dropFinished = Signal(dict)

    def dropEvent(self, event):
        item = self.currentItem()
        if not item:
            return
        old_parent = item.parent()
        if old_parent is None:
            old_index = self.indexOfTopLevelItem(item)
        else:
            old_index = old_parent.indexOfChild(item)
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


class CustomQTextEdit(QTextEdit):

    editingFinished = Signal()

    def focusInEvent(self, event):
        self._base_data = self.toPlainText()
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        if self.toPlainText() != self._base_data:
            self.editingFinished.emit()
        super().focusOutEvent(event)
