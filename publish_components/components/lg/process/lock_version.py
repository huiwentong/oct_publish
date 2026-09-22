from __future__ import annotations

import traceback

from oct.pipeline.path_acs import lock_path
from publish_components.utils.lgt_cmp_publish.lgt_processes import lock_version


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """仅在全部产物和上传成功后，锁定发布根目录及 LGT 版本目录。"""
    try:
        lock_version(process_data, lock_path)
        return ""
    except Exception:
        return traceback.format_exc()
