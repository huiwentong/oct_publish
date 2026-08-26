import traceback
from dataclasses import dataclass, field, asdict
from publish_components.core import InterFace
from qtpy import QtWidgets, QtCore, QtGui
from publish_gui.ui.theme import Color
from publish_core.database.entity import FastSg, SGEntity


class MG:
    @property
    def current_scene(self):
        try:
            import pymel.core as pm
            scene = str(pm.sceneName())
        except:
            scene = ''
        return scene


STYLESHEET = f'''
QWidget  {{
    background-color: {Color.BG_LIGHT};
    border: 1px solid {Color.BORDER};
    border-radius: 6px;
}}
QPushButton {{
    background-color: {Color.BG_CARD};
}}
'''


class RigWidget(QtWidgets.QWidget):
    def __init__(self, input_form, parent=None):
        super().__init__(parent)
        self.input_form = input_form
        main_layout = QtWidgets.QVBoxLayout(self)

        self.ma_widget = QtWidgets.QWidget()
        self.ma_widget.setStyleSheet(STYLESHEET)
        self.select_ma_btn = QtWidgets.QPushButton("选择MA文件")
        self.ma_line = QtWidgets.QLineEdit()
        self.ma_line.setReadOnly(True)
        self.ma_pick_btn = QtWidgets.QPushButton("<<")
        ma_layout = QtWidgets.QHBoxLayout()
        ma_layout.addWidget(self.select_ma_btn)
        ma_layout.addWidget(self.ma_line)
        ma_layout.addWidget(self.ma_pick_btn)
        self.ma_widget.setLayout(ma_layout)

        main_layout.addWidget(self.ma_widget)

        self.on_pick_current()
        self.do_connections()

    def do_connections(self):
        self.ma_pick_btn.clicked.connect(self.on_pick_current)
        self.select_ma_btn.clicked.connect(self.on_pick_workfile)

    def on_pick_workfile(self):
        pick_dialog = QtWidgets.QFileDialog()
        pick_dialog.setViewMode(QtWidgets.QFileDialog.Detail)
        pick_dialog.setNameFilters(["Maya File(*.ma )"])
        pick_dialog.exec_()

        l_files = pick_dialog.selectedFiles()
        if len(l_files) > 0:
            self.ma_line.setText(l_files[0])
            self.input_form.update({"ma_file": l_files[0]})

    def on_pick_current(self):
        scene_path = MG().current_scene
        if scene_path != '':
            self.ma_line.setText(scene_path)
            self.ma_widget.setDisabled(False)
            self.input_form.update({"ma_file": scene_path})


@dataclass
class CompInterface(InterFace):
    submit_form: dict = field(
        default_factory=lambda: {
            "ma_file": True,
        }
    )

    tag_list: list = field(
        default_factory=lambda: [1130, 1129]  # ?
    )

    downstream_dcc_only: str | None = 'Maya'

    def gui_pre_interface(self):
        pass

    def init_ui(self, parent: QtWidgets.QWidget):
        rig_widget = RigWidget(self.input_form)
        publish_layout = QtWidgets.QVBoxLayout(parent.files_group)
        publish_layout.setContentsMargins(0, 0, 0, 0)
        publish_layout.addWidget(rig_widget)
        self.update_version_num(parent)


    def gui_post_interface(self):
        pass


    @staticmethod
    def update_version_num(parent):
        try:
            scene_path = MG().current_scene
            if scene_path != '':
                scene_v = int(scene_path.split('.')[-2][1:])
                v_number = 'v{:03d}'.format(scene_v)
                parent._version_edit.setText(v_number)
        except:
            print(traceback.format_exc())
