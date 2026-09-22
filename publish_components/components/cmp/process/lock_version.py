from __future__ import annotations

import traceback

from oct.pipeline.path_acs import lock_path
from publish_components.utils.lgt_cmp_publish.cmp_processes import (
    is_cmp_dailies_context,
    lock_cmp_version,
)


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """仅在全部产物和上传成功后锁定 CMP Dailies 版本目录。"""
    try:
        if not is_cmp_dailies_context(process_data):
            return ""
        lock_cmp_version(process_data, lock_path)
        return ""
    except Exception:
        return traceback.format_exc()
