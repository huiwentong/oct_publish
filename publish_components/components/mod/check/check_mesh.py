# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.utils as utils
from importlib import reload

from publish_components.utils.maya_utils import mesh_gen as mg
from publish_components.utils.sg_helper import get_asset_kind, UE_SCENE_TAG
reload(mg)

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    检查空mesh节点, 重合面, 无法展开的面, 距离太近的边, 有洞的面
    """

    try:
        # UE 场景资产不做这项检查
        if get_asset_kind(process_data.get('task_id')) != UE_SCENE_TAG:
            def check_meshes() -> str | None:
                """Run all mesh access, checks and result formatting on Maya's main thread."""
                high_node = process_data.get('high','|Root_grp|Geo_grp|high')
                non_manifold_meshes = []
                short_edge_meshes = []
                no_face_meshes = []
                meshes = pm.listRelatives(high_node, allDescendents=True, type='mesh') or []
                for mesh in list(meshes):
                    if mesh.isIntermediateObject():
                        continue

                    if mesh.numFaces() == 0:
                        no_face_meshes.append(mesh)
                        continue

                    # Non-manifold
                    if mg.has_non_manifold(mesh):
                        non_manifold_meshes.append(mesh)

                    # Extremely short edge
                    if mg.has_extremely_short_edge(mesh):
                        short_edge_meshes.append(mesh)

                msg = ""
                if no_face_meshes:
                    msg += "\n发现以下模型没有面：\n{}".format('\n'.join([i.nodeName() for i in no_face_meshes]))

                lamina_faces = mg.find_lamina_faces()
                if lamina_faces:
                    msg += "\n发现以下重合面：\n{}".format(lamina_faces)

                #Non-manifold
                if non_manifold_meshes:
                    msg += "\n 以下模型有无法展开的面:\n{}".format('\n'.join([i.nodeName() for i in non_manifold_meshes]))

                # Extremely short edge
                if short_edge_meshes:
                    msg += "\n 以下模型有长度小于 {} 的边:\n{}".format('0.000010', short_edge_meshes)

                # polygon hole
                hole_faces = mg.find_hole_faces()
                if hole_faces:
                    msg += "\n 发现以下带洞的面: \n{}".format(hole_faces)

                if msg != "":
                    process_data["check_mesh_no_face_meshes"] = no_face_meshes
                    process_data['check_mesh_lamina_faces'] = lamina_faces
                    process_data['check_mesh_non_manifold_meshes'] = non_manifold_meshes
                    process_data['check_mesh_short_edge_meshes'] = short_edge_meshes
                    process_data['check_mesh_hole_faces'] = hole_faces
                    return msg

            result = utils.executeInMainThreadWithResult(check_meshes)
            if result:
                return result

    except Exception:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    检查并修复mesh
    """
    #删除空mesh节点, 删除重合面, 删除无法展开的面, 删除距离太近的边

    def fix_meshes() -> str | None:
        """Run mesh operations and failure cleanup on Maya's main thread."""
        try:
            no_face_meshes = process_data.get('check_mesh_no_face_meshes', [])
            for mesh in no_face_meshes:
                logger.warning('AUTO FIX: 删除没有面的模型节点')
                mg.delete_empty_mesh(mesh)

            lamina_faces = process_data.get('check_mesh_lamina_faces', [])
            if lamina_faces:
                logger.warning('AUTO FIX: 清除重合面')
                mg.delete_lamina_faces()

            #Non-manifold
            non_manifold_meshes = process_data.get('check_mesh_non_manifold_meshes', [])
            if non_manifold_meshes:
                logger.warning('AUTO FIX: 清除无法展开的面')
                mg.delete_non_manifold(non_manifold_meshes)

            # Extremely short edge
            short_edge_meshes = process_data.get('check_mesh_short_edge_meshes', [])
            if short_edge_meshes:
                logger.warning('AUTO FIX: 清除长度小于 0.000010 的边'.format())
                mg.delete_short_edges(short_edge_meshes)

            # History
            mg.clear_selection()
            mg.delete_history()
            mg.clear_selection()

            # polygon hole
            hole_faces = process_data.get('check_mesh_hole_faces', [])
            if hole_faces:
                msg = u'无法自定修复带洞的面: {}'.format(hole_faces)
                logger.error(msg)
                return msg

            mg.clear_selection()

        except Exception:
            try:
                mg.disable_poly_select_constraint()
                mg.clear_selection()
            except Exception:
                pass

            return traceback.format_exc()

    try:
        result = utils.executeInMainThreadWithResult(fix_meshes)
        if result:
            return result
    except Exception:
        return traceback.format_exc()

