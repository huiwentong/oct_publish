from __future__ import annotations

import traceback

from oct.pipeline.path_acs import lock_path
from publish_components.utils.lgt_cmp_publish.cmp_publish_processes import (
    lock_cmp_publish_version,
)
from publish_components.utils.lgt_cmp_publish.files import DEFAULT_FILE_SYSTEM


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """仅在 ShotGrid 上传成功且产物完整后锁定 CMP Publish 版本。"""
    try:
        lock_cmp_publish_version(process_data, DEFAULT_FILE_SYSTEM, lock_path)
        return ""
    except Exception:
        return traceback.format_exc()
