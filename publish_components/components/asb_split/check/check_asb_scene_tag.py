# -*- coding: utf-8 -*-
import traceback

from oct.pipeline.shotgun.models import Task

from publish_components.utils.sg_helper import MAYA_SCENE_TAG_ID, UE_SCENE_TAG_ID


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    检查 ASB 资产是否打了且只打了一个场景标签（Maya场景 / UE场景）
    """
    # get_asset_kind 会把无标签 ASB 回退成 UE 场景、双标签优先按 Maya 场景，
    # 看不出这两种错误，这里直接读原始标签。不提供 fix，标签只能去 SG 上改。
    try:
        entity = Task.get(id=int(process_data['task_id'])).entity
        tag_ids = set()
        for tag in entity.tags or []:
            tag_ids.add(tag['id'] if isinstance(tag, dict) else getattr(tag, 'id', None))

        has_maya = MAYA_SCENE_TAG_ID in tag_ids
        has_ue = UE_SCENE_TAG_ID in tag_ids
        if has_maya and has_ue:
            return u"资产同时打了「Maya场景」和「UE场景」两个标签，请在 SG 上只保留一个后重开发布器"
        if not has_maya and not has_ue:
            return u"资产没有场景标签，请在 SG 上打「Maya场景」或「UE场景」标签后重开发布器"

    except:
        return traceback.format_exc()
