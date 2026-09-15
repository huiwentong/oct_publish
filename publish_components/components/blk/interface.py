# coding=utf-8
"""MK2 Blocking 发布，复用动画接口的拆分任务表单。"""
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

from publish_components.components.ani.interface import CompInterface as AnimationInterface


@dataclass
class CompInterface(AnimationInterface):
    """非 blocking 任务强制使用拆分任务模式。"""

    primary_task: ClassVar[str] = 'blocking'
    runlist: str | None = str(Path(__file__).with_name('runlist.xml'))
