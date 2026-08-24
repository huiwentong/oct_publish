# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
from importlib import reload
from publish_components.utils.maya_utils import mesh_gen as mg
reload(mg)

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    检查并修复mesh
    """
    #规范high下 mesh的名字, 删除空mesh节点, 删除重合面, 删除无法展开的面, 删除距离太近的边

    try:
        high_node = process_data.get('high','|Root_grp|Geo_grp|high')
        non_manifold_meshes = []
        short_edge_meshes = []
        meshes = pm.listRelatives(high_node, allDescendents=True, type='mesh') or []
        for mesh in list(meshes):
            if mesh.isIntermediateObject():
                continue

            if mesh.numFaces() == 0:
                logger.warning('AUTO FIX: 删除没有面的模型节点: {}'.format(mesh))
                mg.delete_empty_mesh(mesh)
                continue

            # Shape name
            transform = mesh.getParent()
            expected_name = '{}Shape'.format(transform.nodeName())
            if mesh.nodeName() != expected_name:
                old_name = str(mesh)
                mesh = mg.normalize_mesh_name(mesh)
                logger.warning('AUTO FIX: 重命名 {} -> {}'.format(old_name, mesh))

            # Non-manifold
            if mg.has_non_manifold(mesh):
                non_manifold_meshes.append(mesh)

            # Extremely short edge
            if mg.has_extremely_short_edge(mesh):
                short_edge_meshes.append(mesh)

        lamina_faces = mg.find_lamina_faces()
        if lamina_faces:
            logger.warning( '发现重合面:\n{}\n开始清除'.format(lamina_faces))
            mg.delete_lamina_faces()

        #Non-manifold
        if non_manifold_meshes:
            logger.warning('AUTO FIX: 发现无法展开的面:\n{}\n开始清除'.format(non_manifold_meshes))
            mg.delete_non_manifold(non_manifold_meshes)

        # Extremely short edge
        if short_edge_meshes:
            logger.warning('AUTO FIX: 发现长度小于 {} 的边:\n{}\n开始清除'.format('0.000010', short_edge_meshes))
            mg.delete_short_edges(short_edge_meshes)

        # History
        mg.clear_selection()
        mg.delete_history()
        mg.clear_selection()

        # polygon hole
        hole_faces = mg.find_hole_faces()
        if hole_faces:
            return u'发现以下带洞的面: {}'.format(hole_faces)

        mg.clear_selection()

    except Exception:
        try:
            mg.disable_poly_select_constraint()
            mg.clear_selection()
        except Exception:
            pass

        return traceback.format_exc()
