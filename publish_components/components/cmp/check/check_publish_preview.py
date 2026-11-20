# -*- coding: utf-8 -*-
import traceback

from publish_components.utils.lgt_cmp_publish.checks import (
    check_cmp_publish_preview,
    publish_context,
)
from publish_components.utils.lgt_cmp_publish.result import to_framework_status
from publish_core.database.entity import SGEntity


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """实时检查 CMP Publish 的 MOV 或完整编号 EXR Cut 序列。"""
    try:
        context = publish_context(process_data)
        entity = context["entity"]
        shot = SGEntity(
            entity["type"],
            entity["id"],
            fields=["sg_ani_cut_in", "sg_ani_cut_out"],
        )
        return to_framework_status(
            check_cmp_publish_preview(process_data, shot_data=shot.raw()),
            logger,
        )
    except Exception:
        return traceback.format_exc()
