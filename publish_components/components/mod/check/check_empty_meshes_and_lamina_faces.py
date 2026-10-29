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
    检查空mesh节点, 重合面
    """
    def uncheck_low(faces):
        bad_face = []
        for f in faces:
            full_path = pm.PyNode(f).node().fullPath()
            if str(full_path).startswith("|Root_grp|Geo_grp|low"):
                continue
            bad_face.append(f)
        return bad_face

    try:
        # UE 场景资产 以及 tag 为 “低模”的时候不做这项检查
        if get_asset_kind(process_data.get('task_id')) != UE_SCENE_TAG and \
            process_data['publish_tag_id'] != 1129:
            def check_meshes() -> str | None:
                """Run all mesh access, checks and result formatting on Maya's main thread."""
                high_node = process_data.get('high','|Root_grp|Geo_grp|high')
                no_face_meshes = []
                meshes = pm.listRelatives(high_node, allDescendents=True, type='mesh') or []
                for mesh in list(meshes):
                    if mesh.isIntermediateObject():
                        continue

                    if mesh.numFaces() == 0:
                        no_face_meshes.append(mesh)
                        continue

                msg = ""
                if no_face_meshes:
                    msg += "\n发现以下模型没有面：\n{}".format('\n'.join([i.nodeName() for i in no_face_meshes]))

                lamina_faces = mg.find_lamina_faces()
                lamina_faces = uncheck_low(lamina_faces)
                if lamina_faces:
                    msg += "\n发现以下重合面：\n{}".format(lamina_faces)

                if msg != "":
                    process_data["check_mesh_no_face_meshes"] = no_face_meshes
                    process_data['check_mesh_lamina_faces'] = lamina_faces
                    return msg
                return None

            result = utils.executeInMainThreadWithResult(check_meshes)
            if result:
                return result

    except Exception:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    删除空mesh节点,重合面
    """
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

            mg.clear_selection()

        except Exception:
            try:
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

