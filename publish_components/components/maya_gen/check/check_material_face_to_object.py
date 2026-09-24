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
    """打断残留的空材质连接，并将单材质模型改为整物体赋材质"""
    try:
        def repair():
            cut = 0
            forced = 0
            n_high = process_data.get("high", "|Root_grp|Geo_grp|high")
            for shape in pm.listRelatives(n_high, ad=True, type="mesh", ni=True, fullPath=True) or []:
                conns = pm.listConnections(shape, type="shadingEngine", c=True, p=True) or []

                # 按实际成员区分：整体赋值 / 按面赋值 / 没有成员（残留的空连接）
                used, face_sgs = set(), set()
                for sg in set(plug.node() for _, plug in conns):
                    for item in pm.sets(sg, q=True) or []:
                        if isinstance(item, pm.MeshFace):
                            if item.node() == shape:
                                used.add(sg)
                                face_sgs.add(sg)
                        elif item == shape or (isinstance(item, pm.nt.Transform) and shape in item.getShapes()):
                            used.add(sg)

                # 改过材质后会残留指向旧 SG 的连接，里面没有这个模型的成员，直接打断
                for shape_plug, sg_plug in conns:
                    if sg_plug.node() in used:
                        continue
                    if pm.isConnected(shape_plug, sg_plug):
                        pm.disconnectAttr(shape_plug, sg_plug)
                    elif pm.isConnected(sg_plug, shape_plug):
                        pm.disconnectAttr(sg_plug, shape_plug)
                    cut += 1
                    logger.warning("AUTO FIX: 打断残留材质连接: {} -> {}".format(shape_plug, sg_plug))

                # 只剩一个材质但按面赋值的，改为整物体赋值
                if len(used) == 1 and face_sgs:
                    sg = used.pop()
                    pm.sets(sg, e=True, forceElement=shape)
                    forced += 1
                    logger.warning("AUTO FIX: 材质改为整物体赋值: {} -> {}".format(shape.longName(), sg.name()))

            return cut, forced

        cut, forced = utils.executeInMainThreadWithResult(repair)
        if not cut and not forced:
            return "没有可自动修复的内容：报错中的模型确实使用了多个材质，请手动改为单个材质整物体赋值"
        logger.info("材质修复完成：打断残留连接 {} 处，整物体赋值 {} 个模型".format(cut, forced))

    except Exception:
        return traceback.format_exc()
