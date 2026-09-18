# -*- coding: utf-8 -*-

import traceback

import maya.cmds as cmds
import maya.mel as mel


def _get_arnold_node_types():
    """获取 mtoa 插件注册的 Arnold 节点类型。"""
    try:
        node_types = mel.eval('pluginInfo -q -dependNode "mtoa";') or []
    except Exception:
        return set()

    if isinstance(node_types, str):
        node_types = [node_types]

    return set(node_types)


def _check_shader_type_is_arnold(description, arnold_node_types):
    """检查 Description 连接的材质是否为 Arnold 材质。"""
    shapes = cmds.listRelatives(description, shapes=True) or []

    if not shapes:
        return True

    sg_nodes = cmds.listConnections(shapes[0], type="shadingEngine") or []

    if not sg_nodes:
        return True

    sg = sg_nodes[0]

    shader = cmds.listConnections(sg + ".aiSurfaceShader", source=True, destination=False) or []

    if not shader:
        shader = cmds.listConnections(sg + ".surfaceShader", source=True, destination=False) or []

    if not shader:
        return True

    shader_type = cmds.nodeType(shader[0])

    return shader_type in arnold_node_types


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查 XGen Description 连接的材质是否为 Arnold 材质。"""
    try:
        palette = process_data.get("xgen_palette_name")
        descriptions = process_data.get("xgen_descriptions", [])

        if not palette:
            return u"没有获取到 XGen Palette 信息"

        if not descriptions:
            return u"没有获取到 XGen Description 信息"

        arnold_node_types = _get_arnold_node_types()

        if not arnold_node_types:
            return u"无法获取 mtoa Arnold 节点类型，请检查 Arnold 插件是否加载"

        bad_descriptions = []

        for description in descriptions:
            if not _check_shader_type_is_arnold(description, arnold_node_types):
                bad_descriptions.append(description.split("|")[-1])

        if bad_descriptions:
            return u"连接了非 Arnold 材质：\n{}".format("\n".join(bad_descriptions))

        return ""

    except Exception:
        return traceback.format_exc()