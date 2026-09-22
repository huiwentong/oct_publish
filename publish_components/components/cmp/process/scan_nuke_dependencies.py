from __future__ import annotations

import traceback

from publish_components.utils.lgt_cmp_publish.cmp_publish_processes import (
    scan_cmp_publish_dependencies,
)


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """从已发布的 Nuke 副本记录 Read、DeepRead 和 Camera2 依赖路径。"""
    try:
        scan_cmp_publish_dependencies(process_data)
        return ""
    except Exception:
        return traceback.format_exc()
