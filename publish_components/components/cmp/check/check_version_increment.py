# -*- coding: utf-8 -*-
import traceback

from publish_components.utils.lgt_cmp_publish.checks import check_version_increment
from publish_components.utils.lgt_cmp_publish.result import to_framework_status


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查待发布版本号是否高于当前 Task 已存在的最高 Version。"""
    try:
        return to_framework_status(check_version_increment(process_data), logger)
    except Exception:
        return traceback.format_exc()
