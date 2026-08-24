# -*- coding: utf-8 -*-
import traceback
from pxr import Usd
import pymel.core as pm
from importlib import reload
from oct.data.usd import append_auto_low
from oct.pipeline.task_context import TaskContext
from publish_components.utils.sg_helper import is_rig_task_omit
reload(append_auto_low)
def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """自动输出并组装low.usd"""

    try:

        task_id = process_data.get("task_id")
        n_low = process_data.get("low", "|Root_grp|Geo_grp|low")
        tc = TaskContext(task_id) or TaskContext.from_env()
        if tc.entity.sg_asset_type == "PROP":
            has_low = False
            is_env_prop = is_rig_task_omit(task_id)
            if pm.objExists(n_low):
                has_low = bool(pm.listRelatives(n_low, allDescendents=True, shapes=True))
            if is_env_prop and not has_low:
                append_auto_low.start(tc.project_name, tc.entity_name)

    except Exception:
        return traceback.format_exc()
