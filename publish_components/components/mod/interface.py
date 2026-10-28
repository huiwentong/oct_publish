import traceback
from dataclasses import dataclass, field, asdict
from publish_components.core import InterFace
from qtpy import QtWidgets, QtCore, QtGui
from publish_gui.ui.theme import Color

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

class ModWidget(QtWidgets.QWidget):
    def __init__(self,input_form, parent=None):
        super().__init__(parent)
        self.input_form = input_form
        self.input_form.update({"zb_file": "test", "ma_file": "test", "extra_files": []})
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

        self.zb_widget = QtWidgets.QWidget()
        self.zb_widget.setStyleSheet(STYLESHEET)
        self.select_zb_btn = QtWidgets.QPushButton("选择ZB文件")
        self.zb_line = QtWidgets.QLineEdit()
        self.zb_line.setReadOnly(True)
        self.zb_pick_btn = QtWidgets.QPushButton("<<")
        zb_layout = QtWidgets.QHBoxLayout()
        zb_layout.addWidget(self.select_zb_btn)
        zb_layout.addWidget(self.zb_line)
        zb_layout.addWidget(self.zb_pick_btn)
        self.zb_widget.setLayout(zb_layout)

        main_layout.addWidget(self.ma_widget)
        main_layout.addWidget(self.zb_widget)

        self.extra_files_widget = QtWidgets.QWidget()
        self.extra_files_widget.setStyleSheet(STYLESHEET)
        extra_files_layout = QtWidgets.QVBoxLayout(self.extra_files_widget)
        self.extra_files_label = QtWidgets.QLabel("附加文件 / 文件夹")
        self.extra_files_label.setStyleSheet("border: none;")
        extra_files_layout.addWidget(self.extra_files_label)
        self.extra_files_list = QtWidgets.QListWidget()
        self.extra_files_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        extra_files_layout.addWidget(self.extra_files_list)

        extra_buttons_layout = QtWidgets.QHBoxLayout()
        self.add_files_btn = QtWidgets.QPushButton("添加文件")
        self.add_folder_btn = QtWidgets.QPushButton("添加文件夹")
        self.remove_files_btn = QtWidgets.QPushButton("移除选中")
        extra_buttons_layout.addWidget(self.add_files_btn)
        extra_buttons_layout.addWidget(self.add_folder_btn)
        extra_buttons_layout.addWidget(self.remove_files_btn)
        extra_files_layout.addLayout(extra_buttons_layout)
        main_layout.addWidget(self.extra_files_widget)
        self.add_extra_paths(list(self.input_form["extra_files"]))

        self.on_pick_current()
        self.do_connections()

    def do_connections(self):
        self.ma_pick_btn.clicked.connect(self.on_pick_current)
        self.select_ma_btn.clicked.connect(self.on_pick_workfile)
        self.select_zb_btn.clicked.connect(self.on_pick_zbfile)
        self.add_files_btn.clicked.connect(self.on_add_extra_files)
        self.add_folder_btn.clicked.connect(self.on_add_extra_folder)
        self.remove_files_btn.clicked.connect(self.on_remove_extra_files)

    def on_add_extra_files(self):
        file_paths, _ = QtWidgets.QFileDialog.getOpenFileNames(self, "添加文件")
        self.add_extra_paths(file_paths)

    def on_add_extra_folder(self):
        folder_path = QtWidgets.QFileDialog.getExistingDirectory(self, "添加文件夹")
        if folder_path:
            self.add_extra_paths([folder_path])

    def add_extra_paths(self, paths):
        existing_paths = {
            self.extra_files_list.item(index).text()
            for index in range(self.extra_files_list.count())
        }
        for path in paths:
            if path and path not in existing_paths:
                item = QtWidgets.QListWidgetItem(path)
                item.setToolTip(path)
                self.extra_files_list.addItem(item)
                existing_paths.add(path)
        self.sync_extra_files()

    def on_remove_extra_files(self):
        for item in self.extra_files_list.selectedItems():
            self.extra_files_list.takeItem(self.extra_files_list.row(item))
        self.sync_extra_files()

    def sync_extra_files(self):
        self.input_form["extra_files"] = [
            self.extra_files_list.item(index).text()
            for index in range(self.extra_files_list.count())
        ]

    def on_pick_zbfile(self):
        pick_dialog = QtWidgets.QFileDialog()
        pick_dialog.setViewMode(QtWidgets.QFileDialog.Detail)
        pick_dialog.setNameFilters(["zbrush File(*.ztl)"])
        pick_dialog.exec_()

        l_files = pick_dialog.selectedFiles()
        if len(l_files) > 0:
            self.zb_line.setText(l_files[0])
            self.input_form.update({"zb_file": l_files[0]})

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
            "zb_file": True,
            "extra_files": True,
        }
    )

    tag_list: list = field(
        default_factory=lambda: [1050, 1129, 1130]
    )

    downstream_dcc_only:str | None = 'Maya'


    def gui_pre_interface(self):
        pass


    def init_ui(self, parent:QtWidgets.QWidget):
        mod_widget = ModWidget(self.input_form)
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
        except:
            print(traceback.format_exc())

if __name__ == "__main__":
    ci = CompInterface(submit_type='Dailies', input_form={'dcc_file': 'sss', 'test': 'dd'}, 
                       process_data={'task_id': 143051}, 
                       dcc_file='cmd'
                       )

    print(asdict(ci))