from __future__ import annotations

import traceback

from publish_components.utils.lgt_cmp_publish.cmp_processes import (
    is_cmp_dailies_context,
    validate_cmp_uat_target,
)
from publish_components.utils.lgt_cmp_publish.modes import (
    validate_process_publish_mode,
)


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """仅允许已批准的 TDTEST CMP 任务执行 Dailies 写入；Publish 模式自动跳过。"""
    try:
        validate_process_publish_mode("cmp", process_data)
        if not is_cmp_dailies_context(process_data):
            return ""
        validate_cmp_uat_target(
            process_data,
            project_id=136,
            entity_id=16735,
            task_id=187851,
        )
        return ""
    except Exception:
        return traceback.format_exc()
