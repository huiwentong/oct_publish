
from qtpy import QtWidgets
from publish_gui.ui.theme import Color, STYLESHEET

def message_dialog(title, message, buttons, parent=None):
    msg_box = QtWidgets.QMessageBox(parent)
    msg_box.setStyleSheet(STYLESHEET)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)

    button_map = {}
    for text in buttons:
        btn = msg_box.addButton(
            text,
            QtWidgets.QMessageBox.ActionRole
        )
        button_map[btn] = text
    msg_box.exec_()
    clicked = msg_box.clickedButton()
    return button_map.get(clicked)



