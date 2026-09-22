# -*- coding: utf-8 -*-
import traceback

from publish_components.utils.lgt_cmp_publish.checks import check_cmp_status, publish_context
from publish_components.utils.lgt_cmp_publish.result import to_framework_status
from publish_core.database.entity import SGEntity


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """实时按 CMP 规则禁止 omt/hld 镜头或任务继续提交。"""
    try:
        context = publish_context(process_data)
        entity_ref = context["entity"]
        task_ref = context["task"]
        entity = SGEntity(
            entity_ref["type"],
            entity_ref["id"],
            fields=["sg_status_list"],
        )
        task = SGEntity(
            task_ref["type"],
            task_ref["id"],
            fields=["sg_status_list"],
        )
        return to_framework_status(
            check_cmp_status(
                process_data,
                entity_status=entity.raw().get("sg_status_list"),
                task_status=task.raw().get("sg_status_list"),
            ),
            logger,
        )
    except Exception:
        return traceback.format_exc()
