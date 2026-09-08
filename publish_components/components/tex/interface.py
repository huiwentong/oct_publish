import traceback
from dataclasses import dataclass, field
from publish_components.core import InterFace
from qtpy import QtWidgets, QtCore, QtGui
from publish_gui.ui.theme import Color
from .tex_dialog import TexWidget, MG

@dataclass
class CompInterface(InterFace):

    submit_form: dict = field(
        default_factory=lambda: {
            "ma_file": True,
            "src_tex_files": True
        }
    )

    tag_list: list = field(
        default_factory=lambda: [952, 1009, 953]
    )

    downstream_dcc_only:str | None = 'Maya'


    def gui_pre_interface(self):
        pass


    def init_ui(self, parent:QtWidgets.QWidget):
        tex_widget = TexWidget(self.input_form)
        publish_layout = QtWidgets.QVBoxLayout(parent.files_group)
        publish_layout.setContentsMargins(0, 0, 0, 0)
        publish_layout.addWidget(tex_widget)
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

