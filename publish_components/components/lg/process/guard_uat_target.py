from __future__ import annotations

import traceback

from publish_components.utils.lgt_cmp_publish.lgt_processes import validate_uat_target
from publish_components.utils.lgt_cmp_publish.modes import (
    validate_process_publish_mode,
)


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """仅允许已批准的 TDTEST LGT 任务执行真实 Dailies 写入。"""
    try:
        validate_process_publish_mode("lg", process_data)
        validate_uat_target(
            process_data,
            project_id=136,
            entity_id=16735,
            task_id=187852,
        )
        return ""
    except Exception:
        return traceback.format_exc()
