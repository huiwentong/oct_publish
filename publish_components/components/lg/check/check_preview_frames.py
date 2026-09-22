# -*- coding: utf-8 -*-
import traceback

from publish_components.utils.lgt_cmp_publish.checks import check_preview_frames
from publish_components.utils.lgt_cmp_publish.result import to_framework_status


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """当使用单帧审核时，检查 EXR 与 PNG 两个文件均真实存在。"""
    try:
        return to_framework_status(check_preview_frames(process_data), logger)
    except Exception:
        return traceback.format_exc()
