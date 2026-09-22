# -*- coding: utf-8 -*-
import traceback

from publish_components.utils.lgt_cmp_publish.checks import check_version_name
from publish_components.utils.lgt_cmp_publish.result import to_framework_status


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查 CMP Version 名是否匹配当前 Shot、Task 与三位版本号。"""
    try:
        return to_framework_status(check_version_name(process_data), logger)
    except Exception:
        return traceback.format_exc()
