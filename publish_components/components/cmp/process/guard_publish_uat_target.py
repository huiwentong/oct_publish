from __future__ import annotations

import traceback

from publish_components.utils.lgt_cmp_publish.publish_target import validate_publish_target
from publish_components.utils.lgt_cmp_publish.modes import (
    validate_process_publish_mode,
)


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """核对合成任务及工程、预览、元数据的发布路径一致性，支持各项目 Publish。"""
    try:
        validate_process_publish_mode("cmp", process_data)
        validate_publish_target(process_data, "cmp", "Publish")
        return ""
    except Exception:
        return traceback.format_exc()
