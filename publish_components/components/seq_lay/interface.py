# -*- coding: utf-8 -*-

"""
整场次批量 Layout 发布 —— 场次（Sequence）上的 lay 任务
"""

import traceback
from dataclasses import dataclass

from qtpy import QtCore, QtWidgets

from publish_components.components.lay.interface import CompInterface as LayInterface, LayWidget


COLUMNS = ['#', 'Shot', 'SG 起始帧', 'SG 结束帧', '场景起始帧', '场景结束帧', '拍屏']


class ShotTable(QtWidgets.QTableWidget):
    """勾选要拆分发布的镜头，选中结果同步到 input_form['shots']"""

    def __init__(self, input_form, project_name, parent=None):
        super().__init__(0, len(COLUMNS), parent)
        self.input_form = input_form
        self.project_name = project_name
        self.setHorizontalHeaderLabels(COLUMNS)
        # 列宽交给表头按内容自适应（样式生效后也会重算），拍屏列占满剩余宽度，长路径中间省略
        header = self.horizontalHeader()
        for col in range(len(COLUMNS) - 1):
            header.setSectionResizeMode(col, QtWidgets.QHeaderView.ResizeToContents)
        header.setStretchLastSection(True)
        self.setTextElideMode(QtCore.Qt.ElideMiddle)
        self.verticalHeader().setVisible(False)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.on_context_menu)
        self.load_shots()
        self.itemChanged.connect(self.sync_form)
        self.sync_form()

    def load_shots(self):
        from publish_components.components.seq_lay.shots import query_shots, scan_scene_shots

        try:
            shots = query_shots(self.project_name, scan_scene_shots())
        except Exception:
            print(traceback.format_exc())
            shots = []

        self.setRowCount(len(shots))
        for row, info in enumerate(shots):
            check_item = QtWidgets.QTableWidgetItem()
            # SG 上找不到 rough_layout 任务的镜头不能发布
            if info['task_id']:
                check_item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
                check_item.setCheckState(QtCore.Qt.Checked)
            else:
                check_item.setFlags(QtCore.Qt.NoItemFlags)
                check_item.setToolTip('SG 上找不到该镜头的 rough_layout 任务')
            self.setItem(row, 0, check_item)

            values = [info['shot'], info['sg_ani_cut_in'], info['sg_ani_cut_out'],
                      info['start_f'], info['end_f'], info['preview']]
            for col, value in enumerate(values, start=1):
                item = QtWidgets.QTableWidgetItem('' if value is None else str(value))
                item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
                if col == 6:
                    item.setToolTip(item.text())
                else:
                    item.setTextAlignment(QtCore.Qt.AlignCenter)
                self.setItem(row, col, item)

    def sync_form(self, *args):
        shots = []
        for row in range(self.rowCount()):
            if self.item(row, 0).checkState() == QtCore.Qt.Checked:
                shots.append({'shot': self.item(row, 1).text(), 'preview': self.item(row, 6).text()})
        self.input_form['shots'] = shots

    def on_context_menu(self, pos):
        row = self.rowAt(pos.y())
        if row >= 0:
            menu = QtWidgets.QMenu(self)
            menu.addAction('替换拍屏', lambda: self.replace_preview(row))
            menu.exec_(self.viewport().mapToGlobal(pos))

    def replace_preview(self, row):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, '替换拍屏', self.item(row, 6).text(), 'Mov Files (*.mov)')
        if file_path:
            # setText 会触发 itemChanged -> sync_form
            self.item(row, 6).setText(file_path)
            self.item(row, 6).setToolTip(file_path)


@dataclass
class CompInterface(LayInterface):
    """ma 选择、发布标签、版本号沿用镜头 lay；Publish 时多一张镜头表格"""

    # Publish 时可以不选预览，由 copy_seq_preview 拼接勾选镜头的拍屏（框架在 GUI / CLI 入口读这个标记）
    publish_preview_optional = True

    def init_ui(self, parent: QtWidgets.QWidget):
        publish_layout = QtWidgets.QVBoxLayout(parent.files_group)
        publish_layout.setContentsMargins(0, 0, 0, 0)
        publish_layout.addWidget(LayWidget(self.input_form))
        # Dailies 只发场次版本，用不到镜头
        if self.submit_type != 'Dailies':
            publish_layout.addWidget(ShotTable(self.input_form, self.task_entity.project.name))
        self.update_version_num(parent)

    def fill_submit_form(self):
        super().fill_submit_form()
        # shots 不放进 submit_form（那里每个字段都要求非空，CLI 不传就会报错）。
        # None 表示没指定，check_shot_versions 会发场景里所有镜头；[] 表示 GUI 一个都没勾。
        self.process_data['shots'] = self.input_form.get('shots')
