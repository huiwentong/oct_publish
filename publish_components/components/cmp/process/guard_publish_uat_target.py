from __future__ import annotations

import traceback

from publish_components.utils.lgt_cmp_publish.cmp_processes import (
    validate_cmp_uat_target,
)
from publish_components.utils.lgt_cmp_publish.modes import (
    validate_process_publish_mode,
)


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """仅允许对已批准的 TDTEST 目标执行 CMP Publish 写入。"""
    try:
        validate_process_publish_mode("cmp", process_data)
        validate_cmp_uat_target(
            process_data,
            project_id=136,
            entity_id=16735,
            task_id=187851,
        )
        return ""
    except Exception:
        return traceback.format_exc()
