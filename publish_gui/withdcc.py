"""
Entry point for the publish GUI application.
"""
import sys
from qtpy.QtWidgets import QApplication
from qtpy.QtCore import Qt
from qtpy import QtWidgets, QtGui, QtGui
import os
from publish_gui.ui import MainWindow
from publish_gui.ui.theme import Color, STYLESHEET


os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.fonts.warning=false")

class ChooseType(QtWidgets.QDialog):
    def __init__(self, /, parent: QtWidgets.QWidget | None):
        super().__init__(parent)
        self.setWindowTitle('选择发布类型')
        self.setMinimumWidth(320)
        self.setStyleSheet(STYLESHEET)
        vlay = QtWidgets.QVBoxLayout(self)

        self.label = QtWidgets.QLabel()
        self.label.setText('选择发布类型')
        vlay.addWidget(self.label)

        self._type_combo = QtWidgets.QComboBox()
        self._type_combo.addItems(["Dailies", "Submit", "Publish"])
        self._type_combo.setCurrentIndex(0)
        vlay.addWidget(self._type_combo)

        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        vlay.addWidget(button_box)

        self._selected_type = "Dailies"

    def accept(self):
        self._selected_type = self._type_combo.currentText()
        super().accept()

    def publish_type(self) -> str:
        return self._selected_type


def run(task_id, dcc=None, parent=None):
    ret = ChooseType(parent).exec_()
    window = MainWindow(dcc)
    window._toolbar._type_combo.setEnabled(False)
    window._form_page._back_btn.setEnabled(False)
    window._toolbar._type_combo.setCurrentIndex(ret)
    task = {'id': task_id}
    window._on_task_selected(task)
    window.show()
    return window

    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    screen = app.primaryScreen()
    window = run(120703)
    if screen:
        center = screen.availableGeometry().center()
        frame = window.frameGeometry()
        frame.moveCenter(center)
        window.move(frame.topLeft())
    sys.exit(app.exec())
