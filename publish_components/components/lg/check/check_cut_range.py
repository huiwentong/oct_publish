# -*- coding: utf-8 -*-
import traceback

from publish_components.utils.lgt_cmp_publish.checks import check_cut_range, publish_context
from publish_components.utils.lgt_cmp_publish.result import to_framework_status
from publish_components.utils.lgt_cmp_publish.shotgun import CUT_FIELDS
from publish_core.database.entity import SGEntity


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查 ShotGrid Cut In/Out、Head In 和 Tail Out 是否完整且范围有效。"""
    try:
        context = publish_context(process_data)
        entity = context["entity"]
        shot = SGEntity(
            entity["type"],
            entity["id"],
            fields=CUT_FIELDS,
        )
        return to_framework_status(
            check_cut_range(process_data, shot.raw()),
            logger,
        )
    except Exception:
        return traceback.format_exc()
