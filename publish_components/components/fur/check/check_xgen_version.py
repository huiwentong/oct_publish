# -*- coding: utf-8 -*-

import re
import traceback

import maya.cmds as cmds
import maya.mel as mel


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查 XGen xgVersion 中的 Maya 版本，不正确则自动修复。"""
    try:
        palette_node = process_data.get("xgen_palette_node")

        if not palette_node:
            return u"没有获取到 XGen Palette 节点信息"

        plug = "{}.xgVersion".format(palette_node)

        if not cmds.objExists(plug):
            return u"XGen Palette 没有 xgVersion 属性：{}".format(palette_node)

        xg_version = cmds.getAttr(plug) or ""
        maya_version = str(mel.eval("about -version;"))

        expected_version = "Maya{}".format(maya_version)

        if expected_version in xg_version:
            return ""

        if logger:
            logger.warning(u"XGen xgVersion 的 Maya 版本错误：{}".format(xg_version))
            logger.warning(u"AUTO FIX: 修改 xgVersion 为 {}".format(expected_version))

        if re.search(r"Maya\d+", xg_version):
            new_xg_version = re.sub(r"Maya\d+", expected_version, xg_version)
        else:
            new_xg_version = expected_version

        cmds.setAttr(plug, new_xg_version, type="string")

        mel.eval("file -save -force;")

        return ""

    except Exception:
        return traceback.format_exc()