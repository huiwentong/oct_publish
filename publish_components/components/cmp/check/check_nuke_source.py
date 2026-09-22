# -*- coding: utf-8 -*-
import traceback

from publish_components.utils.lgt_cmp_publish.checks import check_cmp_nuke_source
from publish_components.utils.lgt_cmp_publish.result import to_framework_status


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查 CMP Publish 当前工程/手动文件来源及任务命名是否有效。"""
    try:
        return to_framework_status(check_cmp_nuke_source(process_data), logger)
    except Exception:
        return traceback.format_exc()
