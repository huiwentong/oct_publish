from __future__ import annotations

import traceback
from functools import partial

from publish_components.utils import images
from publish_components.utils.lgt_cmp_publish.cmp_processes import (
    copy_or_create_cmp_preview,
    create_cmp_review_movie,
)
from publish_components.utils.lgt_cmp_publish.cmp_publish_processes import (
    cmp_publish_cut_duration,
)
from publish_components.utils.lgt_cmp_publish.files import DEFAULT_FILE_SYSTEM
from publish_components.utils.lgt_cmp_publish.lgt_processes import publish_context
from publish_core.database.entity import SGEntity


def _frame_count(path):
    _width, _height, duration = images.get_info_by_ffprobe(path)
    return int(duration or 0)


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """复制 MOV，或由所选 EXR 序列生成最终 CMP Publish 预览 MOV。"""
    try:
        context = publish_context(process_data)
        entity = context["entity"]
        shot = SGEntity(
            entity["type"],
            entity["id"],
            fields=["sg_cut_in", "sg_cut_out", "sg_cut_duration"],
        ).raw()
        # Publish EXR checks are strict against the inclusive Cut range, so the
        # generated review must use the same range even when sg_cut_duration is
        # stale or inconsistent with Cut In/Out.
        shot["sg_cut_duration"] = cmp_publish_cut_duration(shot)
        process_data["shot_data"] = shot
        movie_creator = partial(create_cmp_review_movie, frame_probe=_frame_count)
        copy_or_create_cmp_preview(
            process_data,
            DEFAULT_FILE_SYSTEM,
            movie_creator,
        )
        return ""
    except Exception:
        return traceback.format_exc()
