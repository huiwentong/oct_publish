# -*- coding: utf-8 -*-
import traceback
from importlib import reload
import pymel.core as pm
import maya.utils as utils
from oct.pipeline.task_context import TaskContext
from publish_components.utils import maya_utils
reload(maya_utils)
def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
    检查Root_grp组下 transform节点的中心点是否在世界中心
    """
    try:
        def check():
            task_id = process_data['task_id']
            tc = TaskContext(task_id) or TaskContext.from_env()
            tc.refresh()
            rig_task_status = None
            for t in tc.entity.tasks:
                if t.content == 'rigging':
                    rig_task_status = t.sg_status_list
                    break
            error_nodes = []
            if rig_task_status and rig_task_status != 'omt':
                root = process_data.get("geo", pm.PyNode('|Root_grp'))
                for trans in pm.listRelatives(root, ad=True, type='transform'):
                    rotate_pivot, scale_pivot = trans.getPivots(worldSpace=1)
                    if rotate_pivot.length() != 0 and scale_pivot.length() != 0:
                        error_nodes.append(trans)
            return error_nodes

        err_nodes = utils.executeInMainThreadWithResult(check)
        if len(err_nodes) > 0:
            msg = u"以下节点的中心点不在世界坐标中心：\n{}".format("\n".join([i.nodeName() for i in err_nodes]))
            process_data['rotate_pivot_error_nodes'] = err_nodes
            return msg
    except:
        return traceback.format_exc()

def fix(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    try:
        def _fix():
            error_nodes = process_data.get('rotate_pivot_error_nodes', [])
            for trans in error_nodes:
                logger.warning("AUTO FIX: 设置 '{}' 节点的中心点到世界中心".format(trans.nodeName()))
                trans.setPivots((0, 0, 0), worldSpace=1)

        utils.executeInMainThreadWithResult(_fix)

    except:
        return traceback.format_exc()

