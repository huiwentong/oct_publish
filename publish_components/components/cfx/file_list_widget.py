import os
from qtpy import QtWidgets

class FileListWidget(QtWidgets.QListWidget):
    def __init__(self, parent=None):
        super(FileListWidget, self).__init__(parent)

        self.itemPressed.connect(self.on_item_clicked)

    def mousePressEvent(self, event):
        self._mouse_button = event.button()
        super(FileListWidget, self).mousePressEvent(event)

    def on_item_clicked(self, item):
        try:
            print(item.text(), self._mouse_button.name)
        except:
            print(item.text(), self._mouse_button)

    @property
    def files(self):
        files = []
        for idx in range(self.count()):
            item = self.item(idx)
            files.append(item.text())
        return files

    def all_items(self):
        items = []
        for idx in range(self.count()):
            items.append(self.item(idx))
        return items


