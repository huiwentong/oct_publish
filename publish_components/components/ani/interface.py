# -*- coding: utf-8 -*-

"""
镜头动画发布 —— ani 环节（animation 任务）

继承blk的interface，拆分任务组件逻辑在 blk 里，这里只把主任务名改成 animation。
"""

from dataclasses import dataclass
from typing import ClassVar

from publish_components.components.blk.interface import CompInterface as BlkInterface


@dataclass
class CompInterface(BlkInterface):
    """非 animation 任务强制使用拆分任务模式。"""

    primary_task: ClassVar[str] = 'animation'
