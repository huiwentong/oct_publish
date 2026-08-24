# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查整物体材质赋值，并转换为按面赋材质"""
    try:
        n_high = process_data.get("high", "|Root_grp|Geo_grp|high")
        shapes = pm.listRelatives(n_high, ad=True, type="mesh", ni=True, fullPath=True)
        transforms = {shape.getParent() for shape in shapes}
        sgs = {sg
            for shape in shapes
            for sg in shape.connections(type="shadingEngine")}

        for sg in sgs:
            if sg.name() in ("initialShadingGroup", "initialParticleSE"):
                continue
            for item in pm.sets(sg, q=True) or []:
                if ".f[" in str(item):
                    continue
                node = pm.PyNode(item)
                if isinstance(node, pm.nodetypes.Mesh):
                    shape = node
                    trans = node.getParent()
                else:
                    trans = node
                    mesh_shapes = pm.listRelatives(trans, shapes=True, type="mesh", ni=True, fullPath=True)
                    if not mesh_shapes:
                        continue
                    shape = mesh_shapes[0]
                if trans in transforms:
                    #修复
                    face_count = pm.polyEvaluate(shape, face=True)
                    if not face_count:
                        continue
                    faces = "{}.f[0:{}]".format(shape.longName(), face_count - 1)
                    pm.sets(sg, rm=item)
                    pm.sets(sg, e=True, forceElement=faces)
                    logger.warning("AUTO FIX: 材质已改为按面赋值: {} -> {}".format(shape, sg))

        # Alembic Faceset 名称修复
        for sg in sgs:
            if sg.name() in ("initialShadingGroup", "initialParticleSE"):
                continue
            if sg.hasAttr("AbcFacesetName"):
                sg.attr("AbcFacesetName").set("{}_afn".format(sg.name()))

    except Exception:
        return traceback.format_exc()
