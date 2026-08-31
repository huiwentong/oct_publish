# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.utils as utils
import maya.api.OpenMaya as om

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """查找重叠顶点"""

    try:
        def check():
            data = {}
            n_geo = process_data.get("geo", "|Root_grp|Geo_grp")
            for mesh in pm.listRelatives(n_geo, ad=True, type="mesh", fullPath=True, ni=True):
                mesh = str(mesh)
                sel = om.MSelectionList()
                sel.add(mesh)
                points = om.MFnMesh(sel.getDagPath(0)).getPoints()
                coords = {}
                for i, p in enumerate(points):
                    key = (round(p.x, 6), round(p.y, 6), round(p.z, 6))
                    coords.setdefault(key, []).append(i)

                ids = [
                    group
                    for group in coords.values()
                    if len(group) > 1
                ]

                if ids:
                    data[mesh] = ids

            return data

        error_data = utils.executeInMainThreadWithResult(check)
        process_data["vertex_overlap_error_nodes"] = error_data

        if error_data:
            return "以下模型有重叠顶点:\n{}".format("\n".join(error_data))

    except Exception:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    try:
        error_data = process_data.get("vertex_overlap_error_nodes", {})

        def repair():
            for mesh, groups in error_data.items():
                for ids in groups:
                    vertices = [
                        "{}.vtx[{}]".format(mesh, i)
                        for i in ids
                    ]
                    pm.polyMergeVertex(
                        vertices,
                        d=0.00001,
                        ch=False
                    )

        utils.executeInMainThreadWithResult(repair)

    except Exception:
        return traceback.format_exc()
