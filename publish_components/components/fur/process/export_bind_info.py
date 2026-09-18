# -*- coding: utf-8 -*-

import json
import math
import os
import traceback

import maya.cmds as cmds
import maya.utils as utils
import pymel.core as pm
import xgenm as xg


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """导出 Guide、Curve、Description、HairSystem 的绑定关系，并写入 Curve 属性。"""
    try:
        def process():
            palette = process_data.get("xgen_palette_name", getattr(parent_widget, "xgen_palette_name", ""))
            version_dir = process_data.get("version_dir", getattr(parent_widget, "version_dir", ""))

            if not palette:
                return u"没有获取到 XGen Palette"
            if not version_dir:
                return u"没有获取到 Version 目录"

            # Curve -> HairSystem
            map_curve_hairsys = {}
            curves = pm.listRelatives("Hair_curves_cfx", c=True, ad=True, type="nurbsCurve", ni=True) or []

            for curve_shape in curves:
                follicles = pm.listConnections(curve_shape.create, type="follicle", shapes=True) or []
                curve = curve_shape.getParent().name()

                if not follicles:
                    map_curve_hairsys[curve] = ""
                    continue

                hair_system = pm.listConnections(follicles[0].outHair, shapes=True)[0]
                map_curve_hairsys[curve] = hair_system.name()

            # Guide -> Description
            map_guide_desc = {}
            for description in xg.descriptions(palette):
                for guide in xg.descriptionGuides(description):
                    map_guide_desc[guide] = description

            # HairSystem -> Description
            map_hairsys_desc = {}
            for hair_system in cmds.ls(type='hairSystem') or []:
                parent = cmds.listRelatives(hair_system, p=True)[0]
                map_hairsys_desc[hair_system] = parent.replace('hairSystem_', '')

            # Description -> HairSystem
            map_desc_hairsys = {}
            for description in xg.descriptions(palette):
                hair_system = 'hairSystem_' + description
                map_desc_hairsys[description] = hair_system if cmds.objExists(hair_system) else None

            # Guide -> Curve
            map_guide_curve = {}

            for guide, description in map_guide_desc.items():
                map_guide_curve[guide] = None

                input_mesh = cmds.listConnections(guide + ".inputMesh")
                if input_mesh:
                    xgm_make_guide = input_mesh[0]
                    override = cmds.listConnections(xgm_make_guide + ".override")

                    if override:
                        connected_curve = override[0]
                        long_name = cmds.ls(connected_curve, long=True)[0]

                        if "Hair_curves_cfx" in long_name:
                            map_guide_curve[guide] = connected_curve
                            continue

                hair_system = map_desc_hairsys[description]
                if not hair_system:
                    continue

                hair_system_shape = cmds.listRelatives(hair_system, s=True)[0]
                description_curves = [curve for curve, hs in map_curve_hairsys.items() if hs == hair_system_shape]

                guide_pos = cmds.pointPosition(guide + ".vtx[0]")

                for curve in description_curves:
                    curve_pos = cmds.pointPosition(curve + ".cv[0]")
                    distance = math.sqrt(
                        math.pow(guide_pos[0] - curve_pos[0], 2) +
                        math.pow(guide_pos[1] - curve_pos[1], 2) +
                        math.pow(guide_pos[2] - curve_pos[2], 2)
                    )

                    if distance < 0.001:
                        map_guide_curve[guide] = curve
                        break

            # 将 Guide / Description 信息写到 Curve
            for guide, curve in map_guide_curve.items():
                if not curve or not cmds.objExists(curve):
                    continue

                if not cmds.objExists(curve + ".correspondingGuideName"):
                    cmds.addAttr(curve, longName="correspondingGuideName", dataType="string")
                cmds.setAttr(curve + ".correspondingGuideName", guide, type="string")

                if not cmds.objExists(curve + ".attachedXgenDesc"):
                    cmds.addAttr(curve, longName="attachedXgenDesc", dataType="string")
                cmds.setAttr(curve + ".attachedXgenDesc", map_guide_desc[guide], type="string")

            # Curve 和 Guide 位置无法匹配时，根据 HairSystem 补充 Description
            for curve in map_curve_hairsys:
                if cmds.objExists(curve + ".correspondingGuideName"):
                    continue

                curve_shape = pm.listRelatives(curve, ni=True, c=True)[0]
                follicle = pm.listConnections(curve_shape.create)[0]
                hair_system = pm.listConnections(follicle.outHair, shapes=True)[0].name()
                corresponding_desc = map_hairsys_desc[hair_system]

                cmds.addAttr(curve, longName="correspondingGuideName", dataType="string")
                cmds.setAttr(curve + ".correspondingGuideName", "Not Found", type="string")

                cmds.addAttr(curve, longName="attachedXgenDesc", dataType="string")
                cmds.setAttr(curve + ".attachedXgenDesc", corresponding_desc, type="string")

            bind_info = {
                "map_Curve_HairSys": map_curve_hairsys,
                "map_Guide_Desc": map_guide_desc,
                "map_Guide_Curve": map_guide_curve,
                "map_HairSys_Desc": map_hairsys_desc,
                "map_Desc_HairSys": map_desc_hairsys
            }

            bind_info_path = os.path.join(version_dir, "bind_info.json")
            with open(bind_info_path, "w") as f:
                json.dump(bind_info, f, indent=4)

            process_data["bind_info"] = bind_info
            process_data["bind_info_path"] = bind_info_path

            if parent_widget is not None:
                parent_widget.bind_info_path = bind_info_path

            if logger:
                logger.info(u"Bind Info 输出完成：{}".format(bind_info_path))

            return ""

        result = utils.executeInMainThreadWithResult(process)
        return result or ""

    except Exception:
        return traceback.format_exc()