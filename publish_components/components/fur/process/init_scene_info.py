# -*- coding: utf-8 -*-
import os,traceback
import pymel.core as pm
import maya.utils as utils

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """初始化 Fur 发布所需的场景基础信息。"""
    try:
        def process():
            work_space_root = str(pm.sceneName().dirname())
            xgen_palette_name = pm.ls(type='xgmPalette')[0].name()
            scene_name = str(pm.sceneName().basename())
            process_data.update({"scene_name": scene_name,
                                 "work_space_root": work_space_root,
                                 "xgen_palette_name": xgen_palette_name})

            root_grp = pm.PyNode("Root_grp")
            if root_grp.hasAttr("cocoDescription"):
                root_grp.cocoDescription.unlock()
                pm.deleteAttr(root_grp.cocoDescription)

        utils.executeInMainThreadWithResult(process)
    except Exception:
        return traceback.format_exc()