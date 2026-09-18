# -*- coding: utf-8 -*-

import traceback

import maya.cmds as cmds
import maya.mel as mel


def _get_wrap_nodes():
    """获取场景中的 Wrap 节点。"""
    nodes = mel.eval('ls -long -type "wrap";') or []

    if isinstance(nodes, str):
        nodes = [nodes]

    return nodes


def _get_error_connections(wrap_node):
    """获取 driverPoints 中错误使用 outMesh 的连接。"""
    result = []

    connections = cmds.listConnections(wrap_node + ".driverPoints", source=True, destination=False,
                                       plugs=True, connections=True) or []

    for index in range(0, len(connections), 2):
        if index + 1 >= len(connections):
            break

        dst_plug = connections[index]
        src_plug = connections[index + 1]

        src_node = src_plug.split(".", 1)[0]

        if cmds.nodeType(src_node) != "mesh":
            continue

        if not src_plug.endswith(".outMesh"):
            continue

        result.append((dst_plug, src_plug, src_node))

    return result


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查 Wrap 节点 driverPoints 输入，outMesh 自动改为 worldMesh。"""
    try:
        error_connections = []

        for wrap_node in _get_wrap_nodes():
            for dst_plug, src_plug, src_node in _get_error_connections(wrap_node):
                error_connections.append((wrap_node, dst_plug, src_plug, src_node))

        if not error_connections:
            return ""

        if logger:
            for wrap_node, dst_plug, src_plug, src_node in error_connections:
                logger.warning(u"包裹节点 {} 的 driver 输入不符合规范：{}".format(wrap_node, src_plug))

        errors = []

        for wrap_node, dst_plug, src_plug, src_node in error_connections:
            try:
                world_mesh = src_node + ".worldMesh[0]"

                if logger:
                    logger.warning(u"AUTO FIX: {} -> {}".format(src_plug, world_mesh))

                cmds.disconnectAttr(src_plug, dst_plug)
                cmds.connectAttr(world_mesh, dst_plug, force=True)

            except Exception:
                errors.append(wrap_node)

        if errors:
            return u"以下包裹节点没能自动修复：{}".format(", ".join(sorted(set(errors))))

        return ""

    except Exception:
        return traceback.format_exc()