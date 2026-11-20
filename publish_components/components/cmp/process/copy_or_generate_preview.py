from __future__ import annotations

import traceback
from functools import partial

from publish_components.utils import images
from publish_components.utils.lgt_cmp_publish.cmp_processes import (
    copy_or_create_cmp_preview,
    create_cmp_review_movie,
    is_cmp_dailies_context,
)
from publish_components.utils.lgt_cmp_publish.files import DEFAULT_FILE_SYSTEM
from publish_components.utils.lgt_cmp_publish.lgt_processes import publish_context
from publish_core.database.entity import SGEntity


def _frame_count(path):
    _width, _height, duration = images.get_info_by_ffprobe(path)
    return int(duration or 0)


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """复制所选 CMP MOV，或由图片输入生成最终 Dailies 预览 MOV。"""
    try:
        if not is_cmp_dailies_context(process_data):
            return ""
        context = publish_context(process_data)
        entity = context["entity"]
        shot = SGEntity(
            entity["type"],
            entity["id"],
            fields=["sg_ani_cut_in", "sg_ani_cut_out", "sg_cut_duration"],
        ).raw()
        if not shot.get("sg_cut_duration"):
            cut_in = shot.get("sg_ani_cut_in")
            cut_out = shot.get("sg_ani_cut_out")
            if cut_in is not None and cut_out is not None:
                shot["sg_cut_duration"] = cut_out - cut_in + 1
        process_data["shot_data"] = shot
        movie_creator = partial(
            create_cmp_review_movie,
            frame_probe=_frame_count,
        )
        copy_or_create_cmp_preview(
            process_data,
            DEFAULT_FILE_SYSTEM,
            movie_creator,
        )
        return ""
    except Exception:
        return traceback.format_exc()
