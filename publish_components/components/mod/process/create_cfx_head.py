# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.utils as utils
from oct.pipeline.task_context import TaskContext

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """自动创建 head_cfx_Geo"""

    try:
        def process():
            task_id = process_data.get("task_id")
            body_geo_right = process_data.get("body_geo_right", False)
            tc = TaskContext(task_id) or TaskContext.from_env()
            body_geo = '|Root_grp|Geo_grp|high|body|body_Geo'
            head_cfx_Geo = '|Root_grp|Geo_grp|low|cfx_low|head_cfx_Geo'
            if tc.entity.sg_asset_type == "CH" and body_geo_right and pm.objExists(body_geo):
                if pm.objExists(head_cfx_Geo):
                    pm.delete(head_cfx_Geo)
                dup_mod = pm.duplicate('body_Geo', rr=1, rc=1)[0]
                pm.delete(dup_mod + '.f[10192:26341]')
                pm.rename(dup_mod, 'head_cfx_Geo')
                pm.select('head_cfx_Geo', r=1)
                pm.hyperShade(assign='lambert1')
                pm.setAttr('head_cfx_Geo.v', 0)
                if not pm.objExists('cfx_low'):
                    pm.group(name='cfx_low', em=1)
                    pm.parent('cfx_low', 'low')
                pm.parent('head_cfx_Geo', 'cfx_low')

        utils.executeInMainThreadWithResult(process)

    except Exception:
        return traceback.format_exc()
