# -*- coding: utf-8 -*-
import traceback
import maya.cmds as cmds
import maya.mel as mel
import maya.utils as utils

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """删除 XGen Palette 后导出动力学文件。"""
    try:
        def process():
            version_dir=process_data.get("version_dir")
            entity_name=process_data.get("entity_name")
            palette_node=process_data.get("xgen_palette_node")

            if not version_dir:
                raise RuntimeError(u"没有获取到 version_dir")
            if not entity_name:
                raise RuntimeError(u"没有获取到 entity_name")
            if not palette_node:
                raise RuntimeError(u"没有获取到 xgen_palette_node")
            if not cmds.objExists("Root_grp"):
                raise RuntimeError(u"场景中不存在 Root_grp")

            if cmds.objExists(palette_node):
                cmds.delete(palette_node)

            mel.eval('select -cl;')
            mel.eval('select -r "Root_grp";')

            version_dir=str(version_dir).replace("\\","/").rstrip("/")
            dyn_file="{}/{}.dyn.ma".format(version_dir,entity_name)
            mel.eval('file -force -options "v=0;" -typ "mayaAscii" -pr -es "{}";'.format(dyn_file.replace('"','\\"')))
            process_data["dyn_file"]=dyn_file

            if logger:
                logger.info(u"动力学文件导出完成：{}".format(dyn_file))

        utils.executeInMainThreadWithResult(process)
    except Exception:
        return traceback.format_exc()