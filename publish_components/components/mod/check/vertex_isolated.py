# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.api.OpenMaya as om
import maya.utils as utils
from publish_components.utils.sg_helper import get_asset_kind, UE_SCENE_TAG

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查孤立顶点"""
    try:
        def _check():
            n_high = process_data.get("high", '|Root_grp|Geo_grp|high')
            n_low = process_data.get("low", '|Root_grp|Geo_grp|low')
            nodes = [i for i in [n_high, n_low] if pm.objExists(i)]
            meshes = pm.listRelatives(nodes, ad=True, type="mesh", fullPath=True, ni=True) or []
            data = {}

            for mesh in meshes:
                sel = om.MSelectionList()
                sel.add(str(mesh))
                fn = om.MFnMesh(sel.getDagPath(0))
                used_ids = set(fn.getVertices()[1])
                unused_ids = sorted(set(range(fn.numVertices)) - used_ids)
                if unused_ids:
                    data[str(mesh)] = unused_ids
            return data

        # UE 场景资产（含没打标签的 ASB）不做这项检查
        if get_asset_kind(process_data.get('task_id')) != UE_SCENE_TAG:
            error_data = utils.executeInMainThreadWithResult(_check)
            if error_data:
                process_data["vertex_isolated_error_nodes"] = error_data
                return "以下模型有悬浮在面外的点:\n{}".format(
                    "\n".join("{}: {}".format(mesh, ids) for mesh, ids in error_data.items()))

    except Exception:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    try:
        error_data = process_data.get("vertex_isolated_error_nodes", {})

        def _fix():
            vertices = [
                "{}.vtx[{}]".format(mesh, vtx_id)
                for mesh, ids in error_data.items()
                for vtx_id in ids
            ]

            pm.delete(vertices)

        utils.executeInMainThreadWithResult(_fix)

    except Exception:
        return traceback.format_exc()
