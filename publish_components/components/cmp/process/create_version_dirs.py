from __future__ import annotations

import traceback

from oct.pipeline import path_acs
from publish_components.utils.lgt_cmp_publish.cmp_processes import (
    create_cmp_version_dirs,
    is_cmp_dailies_context,
)
from publish_components.utils.lgt_cmp_publish.files import DEFAULT_FILE_SYSTEM
from publish_components.utils.lgt_cmp_publish.lgt_processes import publish_context


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """创建 CMP Dailies 版本目录和预览目录；已存在时拒绝覆盖。"""
    try:
        if not is_cmp_dailies_context(process_data):
            return ""
        context = publish_context(process_data)
        publish_root = context["publish_root"]
        if DEFAULT_FILE_SYSTEM.dir_exists(publish_root):
            path_acs.unlock_path(publish_root)
        else:
            path_acs.make_dirs(publish_root)
        preview_dir = create_cmp_version_dirs(
            process_data,
            DEFAULT_FILE_SYSTEM,
        )
        path_acs.unlock_path(preview_dir, True)
        return ""
    except Exception:
        return traceback.format_exc()
