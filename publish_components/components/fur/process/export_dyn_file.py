# -*- coding: utf-8 -*-

import traceback
import maya.cmds as cmds
import maya.mel as mel
import maya.utils as utils


def _process(process_data, logger=None):
    """删除 XGen Palette 后导出动力学文件。"""
    version_dir = process_data.get("version_dir")
    entity_name = process_data.get("entity_name")
    palette_node = process_data.get("xgen_palette_node")

    if not version_dir:
        return u"没有获取到 version_dir"
    if not entity_name:
        return u"没有获取到 entity_name"
    if not palette_node:
        return u"没有获取到 xgen_palette_node"

    if cmds.objExists(palette_node):
        cmds.delete(palette_node)

    cmds.select(clear=True)
    cmds.select("Root_grp", r=True)

    dyn_file = "{}/{}.dyn.ma".format(version_dir.rstrip("/"), entity_name)
    mel.eval('file -force -options "v=0;" -typ "mayaAscii" -pr -es "{}";'.format(
        dyn_file.replace('"', '\\"')
    ))

    if logger:
        logger.info(u"动力学文件导出完成：{}".format(dyn_file))
    return ""


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """删除 XGen Palette 后导出动力学文件。"""
    try:
        result = utils.executeInMainThreadWithResult(_process, process_data, logger)
        return result or ""
    except Exception:
        return traceback.format_exc()