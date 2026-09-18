# -*- coding: utf-8 -*-

import re, traceback
import maya.cmds as cmds
import maya.mel as mel
import maya.utils as utils


def _process(process_data, logger=None):
    """导出 Hair_xgenBaseGeo 包裹文件，并清理 Arnold 属性。"""
    version_dir = process_data.get("version_dir")
    entity_name = process_data.get("entity_name")
    if not version_dir:
        return u"没有获取到 version_dir"
    if not entity_name:
        return u"没有获取到 entity_name"

    wrap_file = "{}/{}.wrap.ma".format(version_dir.rstrip("/"), entity_name)

    cmds.select(clear=True)
    cmds.select("Hair_xgenBaseGeo", r=True)
    mel.eval('file -force -options "v=0;" -typ "mayaAscii" -pr -es "{}";'.format(
        wrap_file.replace('"', '\\"')
    ))

    with open(wrap_file, "r") as f:
        ma_data = f.read()

    ma_data = re.sub(r'  setAttr ".ai_translator" -type "string" (.*?);', "", ma_data)

    with open(wrap_file, "w") as f:
        f.write(ma_data)

    if logger:
        logger.info(u"Wrap 文件导出完成：{}".format(wrap_file))
    return ""


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """导出 Hair_xgenBaseGeo 包裹文件，并清理 Arnold 属性。"""
    try:
        result = utils.executeInMainThreadWithResult(_process, process_data, logger)
        return result or ""
    except Exception:
        return traceback.format_exc()