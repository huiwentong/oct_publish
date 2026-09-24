# -*- coding: utf-8 -*-
import traceback
from importlib import reload

import pymel.core as pm
import maya.utils as utils
import maya.api.OpenMaya as om

from publish_components.utils.maya_utils import dialogs
from publish_components.utils.sg_helper import get_asset_kind, UE_SCENE_TAG
reload(dialogs)


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """查找重叠顶点"""

    try:
        def check():
            data = {}
            error_vertices = []
            n_geo = process_data.get("geo", "|Root_grp|Geo_grp")

            for mesh in pm.listRelatives(n_geo, ad=True, type="mesh", fullPath=True, ni=True):
                mesh = str(mesh)
                sel = om.MSelectionList()
                sel.add(mesh)

                dag_path = sel.getDagPath(0)
                fn_mesh = om.MFnMesh(dag_path)
                points = fn_mesh.getPoints(om.MSpace.kWorld)

                coords = {}
                for i, p in enumerate(points):
                    key = (round(p.x, 6), round(p.y, 6), round(p.z, 6))
                    coords.setdefault(key, []).append(i)

                groups = [ids for ids in coords.values() if len(ids) > 1]

                if groups:
                    data[mesh] = groups
                    error_vertices.extend(
                        "{}.vtx[{}]".format(mesh, i)
                        for group in groups
                        for i in group
                    )

            if error_vertices:
                pm.select(error_vertices, r=True)

            return data, error_vertices

        # UE 场景资产不做这项检查
        if get_asset_kind(process_data.get('task_id')) != UE_SCENE_TAG:
            error_data, error_vertices = utils.executeInMainThreadWithResult(check)
            process_data["vertex_overlap_error_nodes"] = error_data

            if error_data:
                display_nodes = list(error_data)[:20]
                msg = "以下模型有重叠顶点，帮你选中了这些点，请判断是否跳过，自动修复点击 'fix'按钮:\n{}".format(
                    "\n".join(display_nodes))
                remaining = len(error_data) - len(display_nodes)
                if remaining:
                    msg += "\n……另有 {} 个模型未显示（共 {} 个）。".format(remaining, len(error_data))
                if parent_widget:
                    result = dialogs.message_dialog("提示", msg, ["跳过检查", "停止提交"], parent=parent_widget)
                    if result and result == "停止提交":
                        return msg
                else:
                    return msg

    except Exception:
        return traceback.format_exc()
    finally:
        utils.executeInMainThreadWithResult(lambda: pm.select(clear=True))


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    try:
        error_data = process_data.get("vertex_overlap_error_nodes", {})

        def find_overlap(mesh):
            sel = om.MSelectionList()
            sel.add(mesh)
            points = om.MFnMesh(sel.getDagPath(0)).getPoints(om.MSpace.kWorld)

            coords = {}
            for i, p in enumerate(points):
                key = (round(p.x, 6), round(p.y, 6), round(p.z, 6))
                coords.setdefault(key, []).append(i)

            return [ids for ids in coords.values() if len(ids) > 1]

        def repair():
            for mesh in error_data:
                # 每合并一次重新检测，避免顶点编号发生变化
                while True:
                    groups = find_overlap(mesh)
                    if not groups:
                        break

                    vertices = [
                        "{}.vtx[{}]".format(mesh, i)
                        for i in groups[0]
                    ]

                    pm.polyMergeVertex(vertices, d=0.00001, ws=True, ch=False)

            pm.select(clear=True)

        utils.executeInMainThreadWithResult(repair)

    except Exception:
        return traceback.format_exc()