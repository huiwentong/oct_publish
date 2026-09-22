# -*- coding: utf-8 -*-
import traceback

from publish_components.utils.lgt_cmp_publish.checks import check_preview_paths
from publish_components.utils.lgt_cmp_publish.result import to_framework_status


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查至少存在一个有效预览文件，PUR 文件不能代替预览。"""
    try:
        return to_framework_status(check_preview_paths(process_data), logger)
    except Exception:
        return traceback.format_exc()
