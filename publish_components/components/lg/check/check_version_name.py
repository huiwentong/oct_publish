# -*- coding: utf-8 -*-
import traceback

from publish_components.utils.lgt_cmp_publish.checks import check_version_name
from publish_components.utils.lgt_cmp_publish.result import to_framework_status


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查 LG Version 名是否与当前 Shot、Step、Task 和三位版本号一致。"""
    try:
        return to_framework_status(check_version_name(process_data), logger)
    except Exception:
        return traceback.format_exc()
