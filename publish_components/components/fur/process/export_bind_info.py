# -*- coding: utf-8 -*-
import json,math,os,traceback
import maya.cmds as cmds
import maya.utils as utils
import pymel.core as pm
import xgenm as xg

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """导出 Guide、Curve、Description、HairSystem 的绑定关系，并写入 Curve 属性。"""
    try:
        def process():
            palette=process_data.get("xgen_palette_name")
            version_dir=process_data.get("version_dir")
            if not palette:
                raise RuntimeError(u"没有获取到 XGen Palette")
            if not version_dir:
                raise RuntimeError(u"没有获取到 Version 目录")

            version_dir=str(version_dir).replace("\\","/").rstrip("/")
            descriptions=xg.descriptions(palette) or []

            map_curve_hairsys={}
            curves=pm.listRelatives("Hair_curves_cfx",c=True,ad=True,type="nurbsCurve",ni=True) or []
            for curve_shape in curves:
                follicles=pm.listConnections(curve_shape.create,type="follicle",shapes=True) or []
                curve=curve_shape.getParent().name()
                if not follicles:
                    map_curve_hairsys[curve]=""
                    continue
                hair_systems=pm.listConnections(follicles[0].outHair,shapes=True) or []
                map_curve_hairsys[curve]=hair_systems[0].name() if hair_systems else ""

            map_guide_desc={}
            for description in descriptions:
                for guide in xg.descriptionGuides(description) or []:
                    map_guide_desc[guide]=description

            map_hairsys_desc={}
            for hair_system in cmds.ls(type="hairSystem") or []:
                parents=cmds.listRelatives(hair_system,p=True) or []
                if not parents:
                    continue
                map_hairsys_desc[hair_system]=parents[0].replace("hairSystem_","")

            map_desc_hairsys={}
            for description in descriptions:
                hair_system="hairSystem_"+description
                map_desc_hairsys[description]=hair_system if cmds.objExists(hair_system) else None

            map_guide_curve={}
            for guide,description in map_guide_desc.items():
                map_guide_curve[guide]=None
                input_mesh=cmds.listConnections(guide+".inputMesh") or []
                if input_mesh:
                    override=cmds.listConnections(input_mesh[0]+".override") or []
                    if override:
                        connected_curve=override[0]
                        long_names=cmds.ls(connected_curve,long=True) or []
                        if long_names and "Hair_curves_cfx" in long_names[0]:
                            map_guide_curve[guide]=connected_curve
                            continue

                hair_system=map_desc_hairsys.get(description)
                if not hair_system:
                    continue

                hair_system_shapes=cmds.listRelatives(hair_system,s=True) or []
                if not hair_system_shapes:
                    continue

                hair_system_shape=hair_system_shapes[0]
                description_curves=[curve for curve,hs in map_curve_hairsys.items() if hs==hair_system_shape]
                guide_pos=cmds.pointPosition(guide+".vtx[0]")

                for curve in description_curves:
                    curve_pos=cmds.pointPosition(curve+".cv[0]")
                    distance=math.sqrt(
                        math.pow(guide_pos[0]-curve_pos[0],2)+
                        math.pow(guide_pos[1]-curve_pos[1],2)+
                        math.pow(guide_pos[2]-curve_pos[2],2)
                    )
                    if distance<0.001:
                        map_guide_curve[guide]=curve
                        break

            for guide,curve in map_guide_curve.items():
                if not curve or not cmds.objExists(curve):
                    continue

                if not cmds.objExists(curve+".correspondingGuideName"):
                    cmds.addAttr(curve,longName="correspondingGuideName",dataType="string")
                cmds.setAttr(curve+".correspondingGuideName",guide,type="string")

                if not cmds.objExists(curve+".attachedXgenDesc"):
                    cmds.addAttr(curve,longName="attachedXgenDesc",dataType="string")
                cmds.setAttr(curve+".attachedXgenDesc",map_guide_desc[guide],type="string")

            for curve,hair_system in map_curve_hairsys.items():
                if cmds.objExists(curve+".correspondingGuideName") or not hair_system:
                    continue

                curve_shapes=pm.listRelatives(curve,ni=True,c=True) or []
                if not curve_shapes:
                    continue

                follicles=pm.listConnections(curve_shapes[0].create) or []
                if not follicles:
                    continue

                hair_systems=pm.listConnections(follicles[0].outHair,shapes=True) or []
                if not hair_systems:
                    continue

                hair_system_name=hair_systems[0].name()
                corresponding_desc=map_hairsys_desc.get(hair_system_name)
                if not corresponding_desc:
                    continue

                cmds.addAttr(curve,longName="correspondingGuideName",dataType="string")
                cmds.setAttr(curve+".correspondingGuideName","Not Found",type="string")

                if not cmds.objExists(curve+".attachedXgenDesc"):
                    cmds.addAttr(curve,longName="attachedXgenDesc",dataType="string")
                cmds.setAttr(curve+".attachedXgenDesc",corresponding_desc,type="string")

            bind_info={
                "map_Curve_HairSys":map_curve_hairsys,
                "map_Guide_Desc":map_guide_desc,
                "map_Guide_Curve":map_guide_curve,
                "map_HairSys_Desc":map_hairsys_desc,
                "map_Desc_HairSys":map_desc_hairsys
            }

            bind_info_path="{}/bind_info.json".format(version_dir)
            with open(bind_info_path,"w",encoding="utf-8") as f:
                json.dump(bind_info,f,indent=4,ensure_ascii=False)

            process_data["bind_info"]=bind_info
            process_data["bind_info_path"]=bind_info_path

            if logger:
                logger.info(u"Bind Info 输出完成：{}".format(bind_info_path))

        utils.executeInMainThreadWithResult(process)
    except Exception:
        return traceback.format_exc()