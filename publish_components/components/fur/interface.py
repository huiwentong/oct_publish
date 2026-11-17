# -*- coding: utf-8 -*-
import traceback
from dataclasses import dataclass, field

from qtpy import QtWidgets
from publish_components.core import InterFace
from publish_gui.ui.theme import Color


class MG:
    @property
    def current_scene(self):
        try:
            import pymel.core as pm
            scene = str(pm.sceneName())
        except Exception:
            scene = ''
        return scene


STYLESHEET = f'''
QWidget {{
    background-color: {Color.BG_LIGHT};
    border: 1px solid {Color.BORDER};
    border-radius: 6px;
}}
QPushButton {{
    background-color: {Color.BG_CARD};
}}
'''


class ModWidget(QtWidgets.QWidget):
    FRAME_START = 1
    FRAME_END = 200
    DEFAULT_STEP = 4

    def __init__(self, input_form, submit_form, parent=None):
        super().__init__(parent)
        self.input_form = input_form
        self.submit_form = submit_form
        self.input_form.update({'ma_file': 'test'})

        main_layout = QtWidgets.QVBoxLayout(self)

        # 原有 MA 文件选择区域
        self.ma_widget = QtWidgets.QWidget()
        self.ma_widget.setStyleSheet(STYLESHEET)
        self.select_ma_btn = QtWidgets.QPushButton('选择MA文件')
        self.ma_line = QtWidgets.QLineEdit()
        self.ma_line.setReadOnly(True)
        self.ma_pick_btn = QtWidgets.QPushButton('<<')

        ma_layout = QtWidgets.QHBoxLayout()
        ma_layout.addWidget(self.select_ma_btn)
        ma_layout.addWidget(self.ma_line)
        ma_layout.addWidget(self.ma_pick_btn)
        self.ma_widget.setLayout(ma_layout)
        main_layout.addWidget(self.ma_widget)

        # Turntable 渲染设置：Start/End 固定，Step 可修改。
        self.turntable_group = QtWidgets.QGroupBox('Turntable 渲染设置')
        turntable_layout = QtWidgets.QHBoxLayout(self.turntable_group)

        self.start_edit = QtWidgets.QLineEdit(str(self.FRAME_START))
        self.start_edit.setReadOnly(True)
        self.start_edit.setFixedWidth(60)

        self.end_edit = QtWidgets.QLineEdit(str(self.FRAME_END))
        self.end_edit.setReadOnly(True)
        self.end_edit.setFixedWidth(60)

        self.frame_step_spin = QtWidgets.QSpinBox()
        self.frame_step_spin.setRange(1, 200)
        self.frame_step_spin.setSingleStep(1)
        self.frame_step_spin.setFixedWidth(70)

        # 如果界面被重建，尽量沿用已经选择的 Step。
        saved_step = self.input_form.get('turntable_frame_step', self.DEFAULT_STEP)
        try:
            saved_step = int(saved_step)
        except (TypeError, ValueError):
            saved_step = self.DEFAULT_STEP
        self.frame_step_spin.setValue(max(1, min(200, saved_step)))

        turntable_layout.addWidget(QtWidgets.QLabel('开始帧'))
        turntable_layout.addWidget(self.start_edit)
        turntable_layout.addSpacing(12)
        turntable_layout.addWidget(QtWidgets.QLabel('结束帧'))
        turntable_layout.addWidget(self.end_edit)
        turntable_layout.addSpacing(12)
        turntable_layout.addWidget(QtWidgets.QLabel('Step'))
        turntable_layout.addWidget(self.frame_step_spin)
        turntable_layout.addStretch()
        main_layout.addWidget(self.turntable_group)

        self.input_form.update({
            'turntable_frame_start': self.FRAME_START,
            'turntable_frame_end': self.FRAME_END,
            'turntable_frame_step': self.frame_step_spin.value(),
        })

        # GUI Component.run() reads submit_form, not input_form.
        # Register the actual integer value instead of a True placeholder.
        self.submit_form['turntable_frame_step'] = self.frame_step_spin.value()

        self.on_pick_current()
        self.do_connections()

    def do_connections(self):
        self.ma_pick_btn.clicked.connect(self.on_pick_current)
        self.select_ma_btn.clicked.connect(self.on_pick_workfile)
        self.frame_step_spin.valueChanged.connect(self.on_frame_step_changed)

    def on_frame_step_changed(self, value):
        value = int(value)
        self.input_form['turntable_frame_step'] = value
        self.submit_form['turntable_frame_step'] = value

    def on_pick_workfile(self):
        pick_dialog = QtWidgets.QFileDialog()
        pick_dialog.setViewMode(QtWidgets.QFileDialog.Detail)
        pick_dialog.setNameFilters(['Maya File(*.ma )'])
        pick_dialog.exec_()

        l_files = pick_dialog.selectedFiles()
        if len(l_files) > 0:
            self.ma_line.setText(l_files[0])
            self.input_form.update({'ma_file': l_files[0]})

    def on_pick_current(self):
        scene_path = MG().current_scene
        if scene_path != '':
            self.ma_line.setText(scene_path)
            self.ma_widget.setDisabled(False)
            self.input_form.update({'ma_file': scene_path})


@dataclass
class CompInterface(InterFace):
    # GUI init_ui() adds turntable_frame_step into submit_form.
    # Keeping only ma_file here avoids requiring a Step value for CLI
    # publishing in InterFace.fill_submit_form().
    submit_form: dict = field(
        default_factory=lambda: {
            'ma_file': True,
        }
    )

    tag_list: list = field(
        default_factory=lambda: [283, 282]
    )

    downstream_dcc_only: str | None = 'Maya'

    def gui_pre_interface(self):
        pass

    def init_ui(self, parent: QtWidgets.QWidget):
        mod_widget = ModWidget(self.input_form, self.submit_form)
        publish_layout = QtWidgets.QVBoxLayout(parent.files_group)
        publish_layout.setContentsMargins(0, 0, 0, 0)
        publish_layout.addWidget(mod_widget)
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
        except Exception:
            print(traceback.format_exc())
