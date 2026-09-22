# -*- coding: utf-8 -*-

"""
镜头 Blocking 发布 —— blk 环节（blocking 任务）

复用 lay 的文件选择界面，补充拆分任务选项；ani 继承本接口，只改主任务名。
"""

from dataclasses import dataclass, field
from typing import ClassVar

from qtpy import QtWidgets

from publish_components.components.lay.interface import CompInterface as LayInterface


@dataclass
class CompInterface(LayInterface):
    """非 blocking 任务强制使用拆分任务模式。"""

    primary_task: ClassVar[str] = 'blocking'
    submit_form: dict = field(default_factory=lambda: {
        'ma_file': True, 'is_split_task': False,
    })

    def fill_submit_form(self) -> None:
        """读取文件和拆分标志，允许普通任务显式传入 False。

        Raises:
            ValueError: 文件缺失，或拆分标志不是布尔值。
        """
        if not self.input_form.get('ma_file'):
            raise ValueError('lack for submitproperty ma_file')
        is_split = self.input_form.get('is_split_task', False)
        if not isinstance(is_split, bool):
            raise ValueError('is_split_task must be a bool')
        self.submit_form.update(
            ma_file=self.input_form['ma_file'],
            is_split_task=is_split or self.task_entity.content != self.primary_task,
        )

    def check_submit_form(self) -> None:
        """校验提交值；子任务在 GUI 与 CLI 中均强制启用拆分模式。"""
        if not isinstance(self.submit_form.get('ma_file'), str) or not self.submit_form['ma_file']:
            raise ValueError('has no property: ma_file value')
        if not isinstance(self.submit_form.get('is_split_task'), bool):
            raise ValueError('is_split_task must be a bool')
        if self.task_entity.content != self.primary_task:
            self.submit_form['is_split_task'] = True

    def init_ui(self, parent: QtWidgets.QWidget) -> None:
        """复用工程文件选择和版本号同步，增加拆分任务选项。

        Args:
            parent: 发布表单页面。
        """
        super().init_ui(parent)
        forced_split = self.task_entity.content != self.primary_task
        self.split_task_check_box = QtWidgets.QCheckBox('是否为拆分任务', parent.files_group)
        self.split_task_check_box.setObjectName('split_task_cb')
        self.split_task_check_box.setChecked(
            forced_split or self.input_form.get('is_split_task', False))
        self.split_task_check_box.setEnabled(not forced_split)
        self.input_form['is_split_task'] = self.split_task_check_box.isChecked()
        # PySide2 连接绑定方法时会哈希接收者；dataclass 实例不可哈希，使用函数转发。
        self.split_task_check_box.toggled.connect(
            lambda checked: self.on_split_task_changed(checked))
        parent.files_group.layout().addWidget(self.split_task_check_box)

    def on_split_task_changed(self, checked: bool) -> None:
        """将复选框值保存到表单，供检查和 SG 更新组件共用。

        Args:
            checked: 当前是否勾选。
        """
        self.input_form['is_split_task'] = checked
