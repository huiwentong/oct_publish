from __future__ import annotations

import traceback

from publish_components.utils.lgt_cmp_publish.cmp_publish_processes import (
    prepare_cmp_publish_source,
)


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """保存表单冻结的当前 Nuke 工程；手动来源模式不修改当前工程。"""
    try:
        prepare_cmp_publish_source(process_data)
        return ""
    except Exception:
        return traceback.format_exc()
