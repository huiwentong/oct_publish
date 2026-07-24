from dataclasses import dataclass, field, asdict
from publish_components.core import InterFace
from qtpy import QtWidgets, QtCore, QtGui




@dataclass
class CompInterface(InterFace):

    submit_form: dict = field(
        default_factory=lambda: {
            "dcc_file": "",
            "test": True
        }
    )
    tag_list: list = field(
        default_factory=lambda: [1130, 1129]
    )


    def gui_pre_interface(self):
        pass


    def init_ui(self, parent):
        vlay = QtWidgets.QVBoxLayout(parent)
        vlay.setContentsMargins(0, 0, 0, 0)
        vlay.setSpacing(0)
        label = QtWidgets.QLabel("This is a test interface for GUI")
        label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        vlay.addWidget(label)
        button = QtWidgets.QPushButton("Click Me")
        button.clicked.connect(lambda: QtWidgets.QMessageBox.information(parent, "Info", "Button Clicked!"))
        vlay.addWidget(button)


    def gui_post_interface(self):
        pass



if __name__ == "__main__":
    ci = CompInterface(submit_type='Dailies', input_form={'dcc_file': 'sss', 'test': 'dd'}, 
                       process_data={'task_id': 143051}, 
                       dcc_file='cmd'
                       )

    print(asdict(ci))