# -*- coding: utf-8 -*-

import os
import re
import traceback

import maya.cmds as cmds
import maya.mel as mel


ABS_PATH_PATTERN = re.compile(r'(?i)^[a-z]:[\\/]')
UNC_PATH_PATTERN = re.compile(r'^(?:\\\\|//)')


def _resolve_xgen_file(palette_node):
    """从 Palette 的 xgFileName 解析实际 .xgen 文件路径。"""
    plug = "{}.xgFileName".format(palette_node)

    if not cmds.objExists(plug):
        return ""

    try:
        xgen_name = cmds.getAttr(plug)
    except Exception:
        return ""

    if not xgen_name:
        return ""

    xgen_name = os.path.expandvars(str(xgen_name)).strip().replace("\\", "/")

    if os.path.isabs(xgen_name) and os.path.isfile(xgen_name):
        return os.path.normpath(xgen_name).replace("\\", "/")

    candidates = []

    scene_path = mel.eval('file -q -sn;') or ""
    if scene_path:
        scene_path = str(scene_path).replace("\\", "/")
        candidates.append(os.path.join(os.path.dirname(scene_path), xgen_name))

    workspace = mel.eval('workspace -q -rd;') or ""
    if workspace:
        workspace = str(workspace).replace("\\", "/")
        candidates.append(os.path.join(workspace, xgen_name))

    for path in candidates:
        path = os.path.normpath(path).replace("\\", "/")

        if os.path.isfile(path):
            return path

    return ""


def _is_absolute_path(value):
    """判断是否为 Windows 盘符路径或 UNC 路径。"""
    value = value.strip()

    if ABS_PATH_PATTERN.match(value):
        return True

    if UNC_PATH_PATTERN.match(value):
        return True

    return False


def _find_absolute_map_paths(xgen_file):
    """仅检查 .xgen 中 MapTextures 块里的绝对路径。"""
    errors = []
    in_map_textures = False

    with open(xgen_file, "r", encoding="utf-8", errors="ignore") as f:
        for line_number, line in enumerate(f, 1):
            text = line.strip()

            if not text:
                continue

            if text == "MapTextures":
                in_map_textures = True
                continue

            if in_map_textures and text == "endAttrs":
                in_map_textures = False
                continue

            if not in_map_textures:
                continue

            parts = text.split(None, 2)

            if len(parts) != 3:
                continue

            obj_name, attr_name, value = parts

            if not _is_absolute_path(value):
                continue

            errors.append(
                u"第 {} 行 {}.{} 引用了绝对路径：{}".format(line_number, obj_name, attr_name, value))

    return errors


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查 XGen MapTextures 中是否存在绝对路径。"""
    try:
        palette_node = process_data.get("xgen_palette_node")

        if not palette_node:
            return u"没有获取到 XGen Palette 节点信息"

        xgen_file = process_data.get("xgen_file", "")

        if not xgen_file or not os.path.isfile(xgen_file):
            xgen_file = _resolve_xgen_file(palette_node)

        if not xgen_file:
            return u"无法找到 Palette {} 对应的 .xgen 文件".format(palette_node)

        process_data["xgen_file"] = xgen_file
        errors = _find_absolute_map_paths(xgen_file)

        if errors:
            return u"XGen MapTextures 中存在绝对路径，请修改为相对路径：\n{}".format("\n".join(errors))

        return ""

    except Exception:
        return traceback.format_exc()