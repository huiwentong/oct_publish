# -*- coding: utf-8 -*-
import os,traceback
import maya.cmds as cmds
import maya.mel as mel
import xgenm as xg

def _flag_true(value):
    return value is True or value==1

def _save_scene():
    """临时绕过 OCT callback 中异常的 cmds.file(q/sn) 查询。"""
    original_file=cmds.file

    def safe_file(*args,**kwargs):
        query=kwargs.get("q",kwargs.get("query",False))
        scene_name=kwargs.get("sn",kwargs.get("sceneName",False))
        short_name=kwargs.get("shn",kwargs.get("shortName",False))
        if _flag_true(query) and _flag_true(scene_name):
            scene=str(mel.eval('file -q -sn;') or "")
            if _flag_true(short_name):
                return scene.replace("\\","/").rsplit("/",1)[-1]
            return scene
        return original_file(*args,**kwargs)

    cmds.file=safe_file
    try:
        mel.eval('file -save -force;')
    finally:
        cmds.file=original_file

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """导出 XGen Palette，并更新 XGen 路径和 HairSystem 状态。"""
    try:
        asset_name=process_data.get("entity_name")
        version_dir=process_data.get("version_dir")
        palette_name=process_data.get("xgen_palette_name")
        palette_node=process_data.get("xgen_palette_node")
        description_nodes=process_data.get("xgen_description_transforms",[])
        origin_paths=process_data.get("origin_paths")

        if not asset_name:
            return u"没有获取到 entity_name"
        if not version_dir:
            return u"没有获取到 version_dir"
        if not palette_name:
            return u"没有获取到 xgen_palette_name"
        if not palette_node:
            return u"没有获取到 xgen_palette_node"
        if origin_paths is None:
            return u"没有获取到 origin_paths"
        if not cmds.objExists(palette_node):
            return u"XGen Palette 节点不存在：{}".format(palette_node)

        core_palettes=set(str(x) for x in (xg.palettes() or []))
        if palette_name not in core_palettes:
            return u"XGen Core 没有加载 Palette：{}，已停止导出以避免 Maya 崩溃".format(palette_name)

        plug=palette_node+".xgFileName"
        if not cmds.objExists(plug):
            return u"XGen Palette 不存在 xgFileName 属性：{}".format(palette_node)

        xgen_file="{}/{}__{}.xgen".format(version_dir.rstrip("/\\"),asset_name,palette_name).replace("\\","/")
        origin_paths["xgFileName"]=cmds.getAttr(plug)

        if logger:
            logger.info(u"开始导出 XGen：{}".format(xgen_file))

        xg.exportPalette(str(palette_name),str(xgen_file))

        if not os.path.isfile(xgen_file):
            return u"XGen 文件未生成：{}".format(xgen_file)

        cmds.setAttr(plug,xgen_file,type="string")
        process_data["origin_paths"]=origin_paths
        process_data["xgen_file"]=xgen_file

        if cmds.objExists(palette_node+".v"):
            cmds.setAttr(palette_node+".v",1)

        for node in description_nodes:
            if cmds.objExists(node+".v"):
                cmds.setAttr(node+".v",1)

        for hair_system in cmds.ls(type="hairSystem") or []:
            cmds.setAttr(hair_system+".simulationMethod",1)
            cmds.setAttr(hair_system+".active",0)

        if logger:
            logger.info(u"XGen 导出完成，开始保存场景")

        _save_scene()

        if logger:
            logger.info(u"XGen 文件导出完成：{}".format(xgen_file))
        return ""
    except Exception:
        return traceback.format_exc()