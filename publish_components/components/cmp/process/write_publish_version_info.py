from __future__ import annotations

import traceback

from publish_components.utils.lgt_cmp_publish.cmp_publish_processes import (
    write_cmp_publish_version_info,
)
from publish_components.utils.lgt_cmp_publish.files import DEFAULT_FILE_SYSTEM


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """原子写入并校验 CMP Publish 的 version_info.json。"""
    try:
        write_cmp_publish_version_info(process_data, DEFAULT_FILE_SYSTEM)
        return ""
    except Exception:
        return traceback.format_exc()
