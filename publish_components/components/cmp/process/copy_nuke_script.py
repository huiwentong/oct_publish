from __future__ import annotations

import traceback

from publish_components.utils.lgt_cmp_publish.cmp_publish_processes import (
    copy_cmp_publish_nuke,
)
from publish_components.utils.lgt_cmp_publish.files import DEFAULT_FILE_SYSTEM


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """将 CMP Publish Nuke 文件复制到版本目录并校验完整性。"""
    try:
        copy_cmp_publish_nuke(process_data, DEFAULT_FILE_SYSTEM)
        return ""
    except Exception:
        return traceback.format_exc()
