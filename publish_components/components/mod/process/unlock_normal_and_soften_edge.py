# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.utils as utils


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    对所有 mesh 解锁法线并柔化边
    """
    try:
        def process():
            n_root = process_data.get('root', '|Root_grp')
            shapes = pm.listRelatives(n_root, ad=True, type='mesh', ni=True) or []
            meshes = set(shape.getParent() for shape in shapes)

            for mesh in meshes:
                logger.warning("AUTO FIX: 修复 '{}' 节点的法线和柔化边".format(mesh))
                pm.polyNormalPerVertex(mesh, ufn=True)
                pm.polySoftEdge(mesh, a=180, ch=False)
            pm.select(cl=True)
        utils.executeInMainThreadWithResult(process)

    except:
        return traceback.format_exc()
