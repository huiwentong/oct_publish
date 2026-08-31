# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.utils as utils


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查整物体材质赋值"""
    try:
        def check():
            data = []

            n_high = process_data.get("high", "|Root_grp|Geo_grp|high")
            shapes = pm.listRelatives(n_high, ad=True, type="mesh", ni=True, fullPath=True)
            transforms = {shape.getParent() for shape in shapes}
            sgs = {sg for shape in shapes
                   for sg in shape.connections(type="shadingEngine")}

            for sg in sgs:
                for item in pm.sets(sg, q=True) or []:
                    if ".f[" in str(item):
                        continue

                    node = pm.PyNode(item)

                    if isinstance(node, pm.nodetypes.Mesh):
                        shape = node
                        trans = node.getParent()
                    else:
                        trans = node
                        shape = pm.listRelatives(trans, shapes=True, type="mesh", ni=True, fullPath=True)[0]

                    if trans in transforms:
                        data.append((sg.name(), str(item), shape.longName()))

            return data

        error_data = utils.executeInMainThreadWithResult(check)
        if error_data:
            process_data["check_facesets_error_nodes"] = error_data
            return "以下模型材质为整物体赋值:\n{}".format(
                "\n".join(
                    "{} -> {}".format(shape, sg)
                    for sg, item, shape in error_data
                )
            )

    except Exception:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """转换为按面赋材质"""
    try:
        def repair():
            error_data = process_data.get("check_facesets_error_nodes", [])
            for sg_name, item, shape in error_data:
                sg = pm.PyNode(sg_name)
                face_count = pm.polyEvaluate(shape, face=True)
                faces = "{}.f[0:{}]".format(shape, face_count - 1)
                pm.sets(sg, rm=item)
                pm.sets(sg, e=True, forceElement=faces)
                logger.warning("AUTO FIX: 材质已改为按面赋值: {} -> {}".format(shape, sg))

        utils.executeInMainThreadWithResult(repair)

    except Exception:
        return traceback.format_exc()
