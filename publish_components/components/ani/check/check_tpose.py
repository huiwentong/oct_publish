# coding=utf-8
import traceback

import maya.utils as utils

from publish_components.utils.maya_utils.animation_checks import check_reference_apose


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None) -> str | None:
    """检查角色 A-Pose 预留帧和控制器数值（沿用旧 MK2 ani 规则，必须通过）。"""
    try:
        result = utils.executeInMainThreadWithResult(check_reference_apose)
        if result:
            return result
    except Exception:
        return traceback.format_exc()
