# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.utils as utils
from importlib import reload
from publish_components.utils.maya_utils import dialogs
from publish_components.utils.maya_utils import mesh_gen as mg
from publish_components.utils.sg_helper import get_asset_kind, UE_SCENE_TAG
reload(mg)

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    无法展开的面, 距离太近的边, 有洞的面
    """

    try:
        # UE 场景资产不做这项检查
        if get_asset_kind(process_data.get('task_id')) != UE_SCENE_TAG:
            def check_meshes() -> str | None:
                """Run all mesh access, checks and result formatting on Maya's main thread."""
                high_node = process_data.get('high','|Root_grp|Geo_grp|high')
                non_manifold_meshes = []
                short_edge_meshes = []
                meshes = pm.listRelatives(high_node, allDescendents=True, type='mesh') or []
                for mesh in list(meshes):
                    if mesh.isIntermediateObject():
                        continue

                    # Non-manifold
                    if mg.has_non_manifold(mesh):
                        non_manifold_meshes.append(mesh)

                    # Extremely short edge
                    if mg.has_extremely_short_edge(mesh):
                        short_edge_meshes.append(mesh)

                msg = ""
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
                    process_data['check_mesh_non_manifold_meshes'] = non_manifold_meshes
                    process_data['check_mesh_short_edge_meshes'] = short_edge_meshes
                    process_data['check_mesh_hole_faces'] = hole_faces
                    return msg
                return None

            result = utils.executeInMainThreadWithResult(check_meshes)
            if result:
                if parent_widget:
                    message = result + "\n请自行判断是否影响下游并修复。如果这些是允许的，请跳过该模块。"
                    selected = dialogs.message_dialog("提示", message, ["跳过检查", "停止提交"], parent=parent_widget)
                    if selected == "停止提交":
                        return message
                else:
                    return result

    except Exception:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    检查并修复mesh
    """
    # 删除无法展开的面, 删除距离太近的边

    def fix_meshes() -> str | None:
        """Run mesh operations and failure cleanup on Maya's main thread."""
        try:
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

