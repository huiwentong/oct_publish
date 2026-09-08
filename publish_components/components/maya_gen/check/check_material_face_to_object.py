# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.utils as utils


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查按面赋材质, 将按面附材质改为按整体附材质"""
    try:
        def check():
            b_sgs = set()
            no_f_meshes = set()
            fix_d = {}

            n_high = process_data.get("high", "|Root_grp|Geo_grp|high")
            shapes = pm.listRelatives(n_high, ad=True, type="mesh", ni=True, fullPath=True)

            for shape in shapes:
                sgs = list(set(pm.listConnections(shape, type="shadingEngine") or []))
                if len(sgs) > 1:
                    no_f_meshes.add(shape.longName())

                for sg in sgs:
                    if sg.name() == "initialShadingGroup":
                        continue

                    for item in pm.sets(sg, q=True) or []:
                        if ".f[" not in str(item):
                            continue
                        b_sgs.add(sg.name())

                        if shape.longName() not in no_f_meshes:
                            fix_d[shape.longName()] = sg.name()

            return b_sgs, no_f_meshes, fix_d

        bad_sgs, no_fix_meshes, fix_data = utils.executeInMainThreadWithResult(check)
        errors = []
        if bad_sgs:
            errors.append("有按面给材质的情况:\n{}".format("\n".join(sorted(bad_sgs))))
        if no_fix_meshes:
            errors.append("以下模型存在多个材质，无法自动修复:\n{}".format("\n".join(sorted(no_fix_meshes))))
        if errors:
            process_data["face_material_fix_data"] = fix_data
            return "\n\n".join(errors)

    except Exception:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """将单材质模型改为整物体赋材质"""
    try:
        def repair():
            fix_data = process_data.get("face_material_fix_data", {})
            for mesh, sg in fix_data.items():
                pm.sets(sg, e=True, forceElement=mesh)
                logger.warning("AUTO FIX: 材质改为整物体赋值: {} -> {}".format(mesh, sg))
        utils.executeInMainThreadWithResult(repair)

    except Exception:
        return traceback.format_exc()
