# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.utils as utils
def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    检查并修复mesh 节点命名符合如下规范:节点名=transform名+Shape
    """

    try:
        high_node = process_data.get('high','|Root_grp|Geo_grp|high')
        meshes = pm.listRelatives(high_node, allDescendents=True, type='mesh') or []
        for mesh in list(meshes):
            if mesh.isIntermediateObject():
                continue

            # Shape name
            transform = mesh.getParent()
            expected_name = '{}Shape'.format(transform.nodeName())
            if mesh.nodeName() != expected_name:
                old_name = str(mesh)
                utils.executeInMainThreadWithResult(lambda :pm.rename(mesh, expected_name))
                logger.warning('AUTO FIX: 重命名 {} -> {}'.format(old_name, mesh))

    except Exception:

        return traceback.format_exc()
