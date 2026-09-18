# -*- coding: utf-8 -*-
import traceback
from dataclasses import dataclass,field
import maya.mel as mel
import xgenm as xg
from publish_components.core import InterFace
from qtpy import QtWidgets
from publish_gui.ui.theme import Color

class MG(object):
    @property
    def current_scene(self):
        try:
            return str(mel.eval('file -q -sn;') or "")
        except Exception:
            return ""

STYLESHEET=f'''
QWidget {{
    background-color: {Color.BG_LIGHT};
    border: 1px solid {Color.BORDER};
    border-radius: 6px;
}}
QPushButton {{
    background-color: {Color.BG_CARD};
}}
'''

class FurWidget(QtWidgets.QWidget):
    def __init__(self,submit_form,process_data,parent=None):
        super().__init__(parent)
        self.submit_form=submit_form
        self.process_data=process_data
        self.submit_form.setdefault("ma_file","")
        self.submit_form.setdefault("cache_dirs",[])
        self.process_data.setdefault("output_turntable",True)
        self.build_ui()
        self.do_connections()
        self.load_cache_dirs()
        self.on_pick_current()
        self.sync_turntable()

    def build_ui(self):
        main_layout=QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(6)

        self.ma_widget=QtWidgets.QWidget()
        self.ma_widget.setStyleSheet(STYLESHEET)
        ma_layout=QtWidgets.QHBoxLayout(self.ma_widget)
        ma_layout.setContentsMargins(8,6,8,6)
        self.select_ma_btn=QtWidgets.QPushButton("选择MA文件")
        self.ma_line=QtWidgets.QLineEdit()
        self.ma_line.setReadOnly(True)
        self.ma_pick_btn=QtWidgets.QPushButton("<<")
        self.ma_pick_btn.setToolTip("获取当前 Maya 场景")
        self.ma_pick_btn.setFixedWidth(40)
        ma_layout.addWidget(self.select_ma_btn)
        ma_layout.addWidget(self.ma_line,1)
        ma_layout.addWidget(self.ma_pick_btn)

        self.cache_widget=QtWidgets.QWidget()
        self.cache_widget.setStyleSheet(STYLESHEET)
        cache_layout=QtWidgets.QVBoxLayout(self.cache_widget)
        cache_layout.setContentsMargins(8,6,8,6)
        cache_layout.setSpacing(4)
        cache_title_layout=QtWidgets.QHBoxLayout()
        self.cache_label=QtWidgets.QLabel("Cache目录（必填）")
        self.add_cache_btn=QtWidgets.QPushButton("添加")
        self.remove_cache_btn=QtWidgets.QPushButton("删除")
        self.add_cache_btn.setFixedWidth(60)
        self.remove_cache_btn.setFixedWidth(60)
        cache_title_layout.addWidget(self.cache_label)
        cache_title_layout.addStretch()
        cache_title_layout.addWidget(self.add_cache_btn)
        cache_title_layout.addWidget(self.remove_cache_btn)
        self.cache_list=QtWidgets.QListWidget()
        self.cache_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        cache_layout.addLayout(cache_title_layout)
        cache_layout.addWidget(self.cache_list)

        self.turntable_widget=QtWidgets.QWidget()
        self.turntable_widget.setStyleSheet(STYLESHEET)
        turntable_layout=QtWidgets.QHBoxLayout(self.turntable_widget)
        turntable_layout.setContentsMargins(8,4,8,4)
        turntable_layout.addStretch()
        self.ttb_check=QtWidgets.QCheckBox("是否输出 Katana Turntable 渲染")
        self.ttb_check.setObjectName("ttb_check")
        self.ttb_check.setChecked(bool(self.process_data.get("output_turntable",True)))
        turntable_layout.addWidget(self.ttb_check)

        main_layout.addWidget(self.ma_widget)
        main_layout.addWidget(self.cache_widget)
        main_layout.addWidget(self.turntable_widget)

    def do_connections(self):
        self.select_ma_btn.clicked.connect(self.on_pick_workfile)
        self.ma_pick_btn.clicked.connect(self.on_pick_current)
        self.add_cache_btn.clicked.connect(self.add_cache_dir)
        self.remove_cache_btn.clicked.connect(self.remove_cache_dir)
        self.ttb_check.toggled.connect(self.on_turntable_changed)

    def on_pick_workfile(self):
        file_path,_=QtWidgets.QFileDialog.getOpenFileName(self,"选择 Maya 文件","","Maya ASCII (*.ma)")
        if not file_path:
            return
        file_path=file_path.replace("\\","/")
        self.ma_line.setText(file_path)
        self.submit_form["ma_file"]=file_path

    def on_pick_current(self):
        scene_path=MG().current_scene
        if not scene_path:
            return
        scene_path=scene_path.replace("\\","/")
        self.ma_line.setText(scene_path)
        self.submit_form["ma_file"]=scene_path

    def load_cache_dirs(self):
        for cache_dir in self.submit_form.get("cache_dirs",[]) or []:
            cache_dir=str(cache_dir).replace("\\","/")
            if cache_dir and cache_dir not in self.get_cache_dirs():
                self.cache_list.addItem(cache_dir)
        self.sync_cache_dirs()

    def add_cache_dir(self):
        cache_dir=QtWidgets.QFileDialog.getExistingDirectory(self,"选择 Cache 目录")
        if not cache_dir:
            return
        cache_dir=cache_dir.replace("\\","/")
        if cache_dir in self.get_cache_dirs():
            return
        self.cache_list.addItem(cache_dir)
        self.sync_cache_dirs()

    def remove_cache_dir(self):
        for item in self.cache_list.selectedItems():
            self.cache_list.takeItem(self.cache_list.row(item))
        self.sync_cache_dirs()

    def get_cache_dirs(self):
        return [self.cache_list.item(i).text() for i in range(self.cache_list.count())]

    def sync_cache_dirs(self):
        self.submit_form["cache_dirs"]=self.get_cache_dirs()

    def sync_turntable(self):
        self.process_data["output_turntable"]=bool(self.ttb_check.isChecked())

    def on_turntable_changed(self,checked):
        self.process_data["output_turntable"]=bool(checked)

@dataclass
class CompInterface(InterFace):
    submit_form:dict=field(default_factory=lambda:{"ma_file":"","cache_dirs":[]})
    tag_list:list=field(default_factory=lambda:[283,282])
    downstream_dcc_only:str|None="Maya"

    def gui_pre_interface(self):
        task=self.task_entity
        step=task.step
        entity=task.entity
        project=task.project
        self.process_data.update({
            "task_id":task.id,
            "task_name":task.content,
            "step_name":step.short_name,
            "step_id":step.id,
            "entity_name":entity.code,
            "entity_id":entity.id,
            "entity_status":entity.sg_status_list,
            "project_name":project.code,
            "project_id":project.id,
            "sg_asset_type":entity.sg_asset_type,
        })
        self.process_data.setdefault("output_turntable",True)

    def init_ui(self,parent:QtWidgets.QWidget):
        self.fur_widget=FurWidget(self.submit_form,self.process_data)
        publish_layout=QtWidgets.QVBoxLayout(parent.files_group)
        publish_layout.setContentsMargins(0,0,0,0)
        publish_layout.addWidget(self.fur_widget)
        self.update_version_num(parent)

    def gui_post_interface(self):
        pass

    @staticmethod
    def update_version_num(parent):
        try:
            scene_path=MG().current_scene
            if not scene_path:
                return
            version_str=scene_path.split(".")[-2]
            if not version_str.startswith("v"):
                return
            parent._version_edit.setText("v{:03d}".format(int(version_str[1:])))
        except Exception:
            print(traceback.format_exc())