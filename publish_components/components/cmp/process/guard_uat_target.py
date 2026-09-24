from __future__ import annotations

import traceback

from publish_components.utils.lgt_cmp_publish.cmp_processes import (
    is_cmp_dailies_context,
)
from publish_components.utils.lgt_cmp_publish.publish_target import validate_publish_target
from publish_components.utils.lgt_cmp_publish.modes import (
    validate_process_publish_mode,
)


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """核对合成任务和正式预览路径的一致性，支持各项目 Dailies；Publish 自动跳过。"""
    try:
        validate_process_publish_mode("cmp", process_data)
        if not is_cmp_dailies_context(process_data):
            return ""
        validate_publish_target(process_data, "cmp", "Dailies")
        return ""
    except Exception:
        return traceback.format_exc()
