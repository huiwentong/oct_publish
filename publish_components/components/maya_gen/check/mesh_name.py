# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.utils as utils
from publish_components.utils.sg_helper import is_rig_task_omit
from oct_maya.utils.maya_utils.shape import is_scene_has_instance
def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    检查并修复mesh 节点命名符合如下规范:节点名=transform名+Shape
    """

    try:
        task_id = process_data['task_id']
        # 如果它的绑定任务状态为弃用，代表它是一个场景，并且场景中有关联复制，那么跳过该检查
        if not is_rig_task_omit(task_id) and not is_scene_has_instance():
            error_nodes = []
            high_node = process_data.get('high','|Root_grp|Geo_grp|high')
            meshes = pm.listRelatives(high_node, allDescendents=True, type='mesh') or []
            for mesh in list(meshes):
                if mesh.isIntermediateObject():
                    continue

                # Shape name
                transform = mesh.getParent()
                expected_name = '{}Shape'.format(transform.nodeName())
                if mesh.nodeName() != expected_name:
                    error_nodes.append(mesh)

            if len(error_nodes) > 0:
                process_data['mesh_name_error_nodes'] = error_nodes
                msg = u"发现以下节点的名字不是 transform + Shape 组成的：\n{}".format('\n'.join([i.nodeName() for i in error_nodes]))
                return msg

    except Exception:

        return traceback.format_exc()

def fix(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    try:
        error_mesh_nodes = process_data.get('mesh_name_error_nodes', [])
        for mesh in error_mesh_nodes:
            old_name = str(mesh)
            transform = mesh.getParent()
            expected_name = '{}Shape'.format(transform.nodeName())
            utils.executeInMainThreadWithResult(lambda: pm.rename(mesh, expected_name))
            logger.warning('AUTO FIX: 重命名 {} -> {}'.format(old_name, mesh))
    except:
        return traceback.format_exc()
