# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.utils as utils
import maya.api.OpenMaya as om

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查并清理悬浮顶点"""
    try:

        n_high = process_data.get("high", '|Root_grp|Geo_grp|high')
        n_low = process_data.get("low", '|Root_grp|Geo_grp|low')
        nodes = [i for i in [n_high, n_low] if pm.objExists(i)]

        def has_unused_vtx(m):
            sel = om.MSelectionList()
            sel.add(str(m))
            fn = om.MFnMesh(sel.getDagPath(0))
            return len(set(fn.getVertices()[1])) < fn.numVertices

        meshes = pm.listRelatives(nodes, ad=True, type="mesh", fullPath=True, ni=True)
        dirty = [m for m in meshes if has_unused_vtx(m)]
        if dirty:
            logger.warning("AUTO FIX: 以下模型有悬浮在面外的点: \n{}\n开始清理".format(dirty))
            pm.select(dirty, r=True)
            pm.mel.eval(
                'polyCleanupArgList 4 { "0","1","0","0","0","0","0","0","0",'
                '"1e-005","0","1e-005","0","1e-005","0","-1","0","1" };'
            )
            pm.delete(dirty, ch=True)
        utils.executeInMainThreadWithResult(lambda: pm.select(cl=1))
    except Exception:
        return traceback.format_exc()
