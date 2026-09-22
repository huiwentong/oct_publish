from __future__ import annotations

import traceback

from publish_components.utils.lgt_cmp_publish.cmp_processes import (
    is_cmp_dailies_context,
    write_cmp_daily_version_info,
)
from publish_components.utils.lgt_cmp_publish.files import DEFAULT_FILE_SYSTEM


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """写入并校验兼容现有格式的 CMP Dailies version_info.json。"""
    try:
        if not is_cmp_dailies_context(process_data):
            return ""
        write_cmp_daily_version_info(process_data, DEFAULT_FILE_SYSTEM)
        return ""
    except Exception:
        return traceback.format_exc()
