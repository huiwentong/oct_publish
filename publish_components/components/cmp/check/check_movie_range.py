# -*- coding: utf-8 -*-
import traceback

from publish_components.utils.lgt_cmp_publish.checks import check_movie_range, publish_context
from publish_components.utils.lgt_cmp_publish.result import to_framework_status
from publish_core.database.entity import SGEntity


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """单个 MOV 时，实时按 ShotGrid Cut duration 检查其帧数。"""
    try:
        context = publish_context(process_data)
        entity = context["entity"]
        shot = SGEntity(
            entity["type"],
            entity["id"],
            fields=["sg_cut_in", "sg_cut_out"],
        )
        return to_framework_status(
            check_movie_range(process_data, shot_data=shot.raw()),
            logger,
        )
    except Exception:
        return traceback.format_exc()
