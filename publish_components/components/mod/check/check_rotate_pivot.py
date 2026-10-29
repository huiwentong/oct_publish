# -*- coding: utf-8 -*-
import traceback
from importlib import reload
import pymel.core as pm
import maya.utils as utils
from oct.pipeline.task_context import TaskContext
from publish_components.utils import maya_utils
from publish_components.utils.sg_helper import get_asset_kind, DEFAULT_ASSET_TAG
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
            is_scene_asset = get_asset_kind(task_id) != DEFAULT_ASSET_TAG
            error_nodes = []
            if not is_scene_asset:
                root = process_data.get("root", '|Root_grp')
                root_node = pm.PyNode(root)
                root_r_pivot, root_s_pivot = root_node.getPivots(worldSpace=1)
                if root_r_pivot.length() > 1e-4 and root_s_pivot.length() > 1e-4:
                    error_nodes.append(root_node)
                for trans in pm.listRelatives(root, ad=True, type='transform'):
                    rotate_pivot, scale_pivot = trans.getPivots(worldSpace=1)
                    # 父级带旋转/缩放时 setPivots 换算回来有 1e-13 量级残差，不能精确比 0。
                    # 容差 1e-4 = 0.0001 厘米（1 微米），离原点不到 1 微米即视为通过
                    if rotate_pivot.length() > 1e-4 and scale_pivot.length() > 1e-4:
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

