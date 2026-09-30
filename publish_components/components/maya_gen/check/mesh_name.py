# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.utils as utils
from oct.pipeline.task_context import TaskContext
from publish_components.utils.maya_utils import dialogs
from publish_core.database.entity import get_step_short_name
from oct_maya.utils.maya_utils.shape import is_scene_has_instance
from publish_components.utils.sg_helper import get_asset_kind, DEFAULT_ASSET_TAG


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    检查并修复mesh 节点命名符合如下规范:节点名=transform名+Shape
    """

    try:
        def check():
            er_nodes = []
            high_node = process_data.get('high','|Root_grp|Geo_grp|high')
            meshes = pm.listRelatives(high_node, allDescendents=True, type='mesh') or []
            for mesh in list(meshes):
                if mesh.isIntermediateObject():
                    continue
                # Shape name
                transform = mesh.getParent()
                expected_name = '{}Shape'.format(transform.nodeName())
                if mesh.nodeName() != expected_name:
                    er_nodes.append(mesh)
            return er_nodes

        task_id = process_data['task_id']
        tc = TaskContext(task_id) or TaskContext.from_env()
        step_short_name = get_step_short_name(tc.step)
        is_scene_asset = get_asset_kind(task_id) != DEFAULT_ASSET_TAG
        # 场景资产带关联复制时，instance 共享同一个 shape，名字对不齐也改不了，只有这种情况跳过；
        # 普通资产不管有没有关联复制都要查
        if not (is_scene_asset and is_scene_has_instance()):
            error_nodes = utils.executeInMainThreadWithResult(check)
            if len(error_nodes) > 0:
                msg = u"发现以下节点的名字不是 transform + Shape 组成的：\n{}".format(
                    '\n'.join([i.nodeName() for i in error_nodes]))
                if step_short_name == 'fur' and parent_widget:
                    msg += ("请reload mod文件后，再次检查!\n"
                            "还是报错，请告知协调人员 联系 mod 制作人员检查以上节点！！")
                    result = dialogs.message_dialog("提示", msg, ["跳过检查", "停止提交"], parent=parent_widget)
                    if result == "停止提交":
                        return msg

                else:
                    process_data['mesh_name_error_nodes'] = error_nodes
                    return msg

    except Exception:

        return traceback.format_exc()

def fix(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    try:
        def _fix():
            error_mesh_nodes = process_data.get('mesh_name_error_nodes', [])
            for mesh in error_mesh_nodes:
                old_name = str(mesh)
                transform = mesh.getParent()
                expected_name = '{}Shape'.format(transform.nodeName())
                pm.rename(mesh, expected_name)
                logger.warning('AUTO FIX: 重命名 {} -> {}'.format(old_name, mesh))
        utils.executeInMainThreadWithResult(_fix)
    except:
        return traceback.format_exc()
