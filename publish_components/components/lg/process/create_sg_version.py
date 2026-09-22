from __future__ import annotations

import traceback

from publish_components.utils import create_shot_mov, images
from publish_components.utils.lgt_cmp_publish.files import DEFAULT_FILE_SYSTEM
from publish_components.utils.lgt_cmp_publish.lgt_processes import (
    create_shotgrid_version,
    prepare_sg_upload_movie,
)
from publish_core.database.core import FastSg


def _frame_count(path):
    _width, _height, duration = images.get_info_by_ffprobe(path)
    return int(duration or 0)


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """创建 LGT Dailies Version、上传预览并加入当天播放列表。"""
    try:
        upload_movie = prepare_sg_upload_movie(
            process_data,
            DEFAULT_FILE_SYSTEM,
            create_shot_mov.convert_nzt_nuke_mov,
        )
        create_shotgrid_version(
            process_data,
            FastSg().client,
            _frame_count,
            upload_movie,
        )
        return ""
    except Exception:
        return traceback.format_exc()
