from __future__ import annotations

import traceback

from publish_components.utils.lgt_cmp_publish.files import DEFAULT_FILE_SYSTEM
from publish_components.utils.lgt_cmp_publish.lgt_processes import copy_thumbnail


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """使用 EXR 与 PNG 单帧审核时，复制可选的 PNG 缩略图。"""
    try:
        copy_thumbnail(process_data, DEFAULT_FILE_SYSTEM)
        return ""
    except Exception:
        return traceback.format_exc()
