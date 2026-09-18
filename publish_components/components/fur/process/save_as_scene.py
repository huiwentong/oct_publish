# -*- coding: utf-8 -*-

import os
import re
import traceback

import maya.cmds as cmds
import maya.mel as mel
import maya.utils as utils


def _get_current_scene():
    """获取当前 Maya 场景路径。"""
    scene_path = mel.eval('file -q -sn;') or ""
    return str(scene_path).replace("\\", "/")


def _save_next_version(process_data, logger=None):
    """将当前 Maya ASCII 场景升一个版本并保存。"""
    scene_path = _get_current_scene()

    if not scene_path:
        raise RuntimeError(u"当前 Maya 场景尚未保存")

    file_name = os.path.basename(scene_path)
    base_name, ext = os.path.splitext(scene_path)

    if ext.lower() != ".ma":
        raise RuntimeError(u"Fur 发布只支持 Maya ASCII 文件：{}".format(scene_path))

    match = re.search(r"\.v(\d+)$", base_name)

    if not match:
        raise RuntimeError(u"当前场景文件名中没有合法版本号：{}".format(file_name))

    old_version = "v{}".format(match.group(1))
    new_version = "v{:03d}".format(int(match.group(1)) + 1)

    new_base_name = (base_name[:match.start()] + "." + new_version)
    new_scene_path = (new_base_name + ext).replace("\\", "/")

    if os.path.exists(new_scene_path):
        raise RuntimeError(u"目标版本已经存在，停止覆盖：{}".format(new_scene_path))

    cmds.file(rename=new_scene_path)

    cmds.file(save=True, force=True, type="mayaAscii")

    process_data["old_version"] = old_version
    process_data["new_version"] = new_version
    process_data["saved_file"] = new_scene_path

    if logger:
        logger.info(u"场景升版：{} -> {}".format(old_version, new_version))
        logger.info(u"保存场景：{}".format(new_scene_path))


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """将当前 Fur Maya 场景升一个版本并保存。"""
    try:
        utils.executeInMainThreadWithResult(_save_next_version, process_data, logger)
        return ""

    except Exception:
        return traceback.format_exc()