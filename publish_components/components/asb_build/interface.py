# -*- coding: utf-8 -*-
"""
ASB 组装发布 —— mod 环节下 ASB 资产的 model 任务。

把已经拆分并发布过的子资产 USD 组装回总资产，
导出 ASB 的 USD、建立 component / component version 并关联到版本。

迁移自老 publish_tool: depts/mk2/mod_asb
表单和 lay 一样只有一个工程文件输入，直接复用 lay 的界面。
"""
from dataclasses import dataclass, field

from publish_components.components.lay.interface import CompInterface as LayInterface


@dataclass
class CompInterface(LayInterface):

    # 283=正式 282=测试，与 asb_split 保持一致
    tag_list: list = field(
        default_factory=lambda: [283, 282]
    )
