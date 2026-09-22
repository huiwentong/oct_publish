# -*- coding: utf-8 -*-
"""
ASB 拆分发布 —— mod 环节下 ASB 资产的 assembly 任务。

把 ASB 总场景按拆分标记切成多个子资产，在 SG 上建资产和 model 任务，
再把每个子资产的导出任务提交到 Deadline 农场。

迁移自老 publish_tool: depts/mk2/asb
表单和 lay 一样只有一个工程文件输入，直接复用 lay 的界面。
"""
from dataclasses import dataclass, field

from publish_components.components.lay.interface import CompInterface as LayInterface


@dataclass
class CompInterface(LayInterface):

    # 283=正式 282=测试
    # 老 set_tags.py 里没有 asb 分支，下拉框保留 widget_file.ui 的预设项（测试/正式），
    # 与同样没有专属标签的 cfx / dyn / efx 取值一致
    tag_list: list = field(
        default_factory=lambda: [283, 282]
    )
