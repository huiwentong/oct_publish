from __future__ import annotations

import traceback

from publish_components.utils import create_shot_mov
from publish_components.utils.lgt_cmp_publish.files import DEFAULT_FILE_SYSTEM
from publish_components.utils.lgt_cmp_publish.lgt_processes import copy_or_create_preview


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """复制所选 MOV，或由图片输入生成最终 LGT 审核预览 MOV。"""
    try:
        copy_or_create_preview(
            process_data,
            DEFAULT_FILE_SYSTEM,
            create_shot_mov.create,
        )
        return ""
    except Exception:
        return traceback.format_exc()
