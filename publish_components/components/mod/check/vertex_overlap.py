# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.utils as utils
import maya.api.OpenMaya as om

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """查找重叠顶点"""

    try:
        def check():
            bad_meshs = {}
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

                vertices = [
                    "{}.vtx[{}]".format(mesh, i)
                    for ids in coords.values()
                    if len(ids) > 1
                    for i in ids
                ]

                if vertices:
                    logger.warning("AUTO FIX: 自动合并‘{}’的重叠点".format(mesh))
                    pm.polyMergeVertex(vertices, d=0.00001, ch=False)
            pm.delete(bad_meshs, ch=True)
        utils.executeInMainThreadWithResult(check)

    except Exception:
        return traceback.format_exc()
