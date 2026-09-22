# -*- coding: utf-8 -*-
import traceback

from publish_components.utils.lgt_cmp_publish.checks import check_rv
from publish_components.utils.lgt_cmp_publish.result import to_framework_status


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查 RV、RVIO 和 RVLS 是否安装，并确认 RVIO 没有许可证错误。"""
    try:
        return to_framework_status(check_rv(process_data), logger)
    except Exception:
        return traceback.format_exc()
