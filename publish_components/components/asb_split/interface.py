# -*- coding: utf-8 -*-
"""
ASB 拆分发布 —— mod 环节下 ASB 资产的 assembly 任务。

把 ASB 总场景按拆分标记切成多个子资产，在 SG 上建资产和 model 任务，
再把每个子资产的导出任务提交到 Deadline 农场。

迁移自老 publish_tool: depts/mk2/asb
表单和 lay 一样只有一个工程文件输入，直接复用 lay 的界面。
"""
from dataclasses import dataclass, field

from qtpy import QtWidgets

from publish_components.components.lay.interface import CompInterface as LayInterface
from publish_components.utils.sg_helper import (
    MAYA_SCENE_TAG,
    UE_SCENE_TAG,
    get_asset_kind,
)
from publish_gui.ui.theme import Color


@dataclass
class CompInterface(LayInterface):

    # 283=正式 282=测试
    # 老 set_tags.py 里没有 asb 分支，下拉框保留 widget_file.ui 的预设项（测试/正式），
    # 与同样没有专属标签的 cfx / dyn / efx 取值一致
    tag_list: list = field(
        default_factory=lambda: [283, 282]
    )

    def init_ui(self, parent: QtWidgets.QWidget) -> None:
        """复用工程文件表单，并显示与发布流程一致的 ASB 场景分类。"""
        super().init_ui(parent)
        info_group = parent._version_name_label.parentWidget()
        row = info_group.findChild(QtWidgets.QWidget, "asb_scene_kind_row")
        if row is None:
            # 兼容已打开的发布器中由旧版界面创建的标题。
            old_label = info_group.findChild(QtWidgets.QLabel, "asb_scene_kind_label")
            if old_label is not None:
                old_label.hide()
                old_label.deleteLater()
            row = QtWidgets.QWidget(info_group)
            row.setObjectName("asb_scene_kind_row")
            row.setFixedHeight(35)
            row.setStyleSheet("background: transparent; border: none;")
            layout = QtWidgets.QHBoxLayout(row)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(8)
            title = QtWidgets.QLabel("Asset Tag:")
            title.setFixedWidth(100)
            layout.addWidget(title)
            layout.addSpacing(40)
            label = QtWidgets.QLabel()
            label.setObjectName("asb_scene_kind_label")
            label.setStyleSheet(
                f"color: {Color.TEXT_SECONDARY}; background: transparent;"
            )
            layout.addWidget(label, stretch=1)
            info_group.layout().insertWidget(0, row)
            # build_info_page 切换任务时会清空发布标签列表；只在创建控件时连接，
            # 隐藏旧 ASB 信息，同时允许返回检查页后继续显示当前任务的标签。
            tag_model = parent._tag_combo.model()
            tag_model.rowsRemoved.connect(row.hide)
            tag_model.modelReset.connect(row.hide)
        label = row.findChild(QtWidgets.QLabel, "asb_scene_kind_label")
        try:
            kind = get_asset_kind(self.task_entity.id)
        except Exception as exc:
            label.setText("读取失败")
            label.setToolTip("无法读取资产场景标签，请检查连接后重新打开发布器。")
            self.log.error(f"读取 ASB 场景标签失败（Task {self.task_entity.id}）：{exc}")
        else:
            name = {
                MAYA_SCENE_TAG: "Maya场景",
                UE_SCENE_TAG: "UE场景",
            }.get(kind, "未识别场景类型")
            label.setText(name)
            label.setToolTip(
                "显示本次发布采用的场景分类；ASB 未设置场景标签时默认按 UE 场景处理。\n"
                "在 SG 修改标签后，请重新打开发布器以刷新缓存。"
            )
        row.show()
