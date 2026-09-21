# -*- coding: utf-8 -*-
import os,traceback
import maya.cmds as cmds
import maya.mel as mel
import maya.utils as utils

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """初始化 Fur 发布所需的场景基础信息。"""
    try:
        def get_scene_path():
            """获取当前 Maya 场景路径，优先复用 save_as_scene 的结果。"""
            scene_path=process_data.get("saved_file","")
            if not scene_path:
                scene_path=mel.eval('file -q -sn;') or ""
            return str(scene_path).replace("\\","/")

        def clean_root_description():
            """删除 Root_grp 上旧流程遗留的 cocoDescription 属性。"""
            attr="Root_grp.cocoDescription"
            if cmds.objExists(attr):
                try:
                    cmds.setAttr(attr,lock=False)
                except Exception:
                    pass
                cmds.deleteAttr(attr)

        def process():
            scene_path=get_scene_path()
            if not scene_path:
                raise RuntimeError(u"当前 Maya 场景尚未保存")
            if not process_data.get("xgen_palette_name"):
                raise RuntimeError(u"没有获取到 XGen Palette 信息")
            if not process_data.get("xgen_descriptions"):
                raise RuntimeError(u"没有获取到 XGen Description 信息")

            process_data["work_space_root"]=os.path.dirname(scene_path).replace("\\","/")
            process_data["scene_name"]=os.path.basename(scene_path)

            clean_root_description()

            if logger:
                logger.info(u"初始化 Fur 场景信息：scene={}, palette={}, descriptions={}".format(
                    process_data["scene_name"],
                    process_data["xgen_palette_name"],
                    len(process_data["xgen_descriptions"])
                ))

        utils.executeInMainThreadWithResult(process)
    except Exception:
        return traceback.format_exc()