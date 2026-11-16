# -*- coding: utf-8 -*-
import traceback

import maya.utils as utils

from oct.pipeline.task_context import TaskContext
from publish_components.utils.maya_utils import asb_build


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查新版 ASB 的 Stage 根下只放子资产，不能有 group"""
    # collect_components 按路径段数区分子资产和深层覆盖：group 下的子资产落在第 3 段，
    # 没有变换覆盖时会被当成覆盖静默丢掉；group 自己设了 kind 又会因缺引用报错。所以在这里拦住。
    # 旧架构由 check_arch_is_new 拦截，这里只看新架构。
    try:
        tc = TaskContext(process_data['task_id'])

        def check():
            _, legacy, proxies = asb_build.scene_info(tc.entity_name)
            if legacy:
                return []
            stage = asb_build.stage_for(proxies[0])
            return [prim.GetPath().pathString for prim in stage.GetPseudoRoot().GetChildren()
                    if not prim.HasAuthoredReferences()]

        groups = utils.executeInMainThreadWithResult(check)
        if groups:
            return (u"ASB Stage 根下不能有 group，请把里面的子资产移到 Stage 根下后删掉 group：\n"
                    + u"\n".join(groups))
    except Exception:
        return traceback.format_exc()
