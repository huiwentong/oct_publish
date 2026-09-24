# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.utils as utils

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
        is_scene_asset = get_asset_kind(task_id) != DEFAULT_ASSET_TAG
        # 场景资产带关联复制时，instance 共享同一个 shape，名字对不齐也改不了，只有这种情况跳过；
        # 普通资产不管有没有关联复制都要查
        if not (is_scene_asset and is_scene_has_instance()):
            error_nodes = utils.executeInMainThreadWithResult(check)
            if len(error_nodes) > 0:
                process_data['mesh_name_error_nodes'] = error_nodes
                msg = u"发现以下节点的名字不是 transform + Shape 组成的：\n{}".format(
                    '\n'.join([i.nodeName() for i in error_nodes]))
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
