from __future__ import annotations

import traceback

from publish_components.utils.lgt_cmp_publish.cmp_publish_processes import (
    version_up_cmp_workfile,
)
from publish_components.utils.lgt_cmp_publish.files import DEFAULT_FILE_SYSTEM


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """发布成功后创建下一版工作文件；GUI 打开它，CLI 只返回路径。"""
    try:
        open_script = (lambda path: None) if process_data.get("is_cli") else None
        version_up_cmp_workfile(
            process_data,
            DEFAULT_FILE_SYSTEM,
            open_script=open_script,
        )
        return ""
    except Exception:
        return traceback.format_exc()
