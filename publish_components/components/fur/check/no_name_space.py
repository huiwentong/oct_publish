# -*- coding: utf-8 -*-

import traceback
import maya.cmds as cmds
import maya.mel as mel


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查并清理非 Reference 节点的命名空间。"""
    try:
        namespace_nodes = []
        node_names = []

        all_nodes = mel.eval('ls -long;') or []
        if isinstance(all_nodes, str):
            all_nodes = [all_nodes]

        for node in all_nodes:
            if not cmds.objExists(node):
                continue

            try:
                if cmds.nodeType(node) == 'reference':
                    continue
                if cmds.referenceQuery(node, isNodeReferenced=True):
                    continue
            except Exception:
                pass

            if is_under_assembly_reference(node):
                continue

            short_name = node.split('|')[-1]
            if ':' not in short_name:
                continue

            if delete_unused_shaders(node, logger):
                continue

            namespace_nodes.append(node)
            node_names.append(node)

        if not namespace_nodes:
            return ""

        if logger:
            logger.warning(u"发现 {} 个带命名空间的节点：{}".format(len(node_names), ', '.join(node_names)))

        # DAG 节点先处理最深层，避免父节点重命名后导致子节点路径失效
        namespace_nodes.sort(key=lambda x: x.count('|'), reverse=True)

        cant_rename = []

        for node in namespace_nodes:
            if not cmds.objExists(node):
                continue

            try:
                old_name = node.split('|')[-1]
                new_name = old_name.split(':')[-1]

                cmds.lockNode(node, lock=False)
                cmds.rename(node, new_name)

                if logger:
                    logger.warning(u"AUTO FIX: 清理节点命名空间 {}".format(old_name))

            except Exception:
                cant_rename.append(node)

        if cant_rename:
            name_str = ', '.join(cant_rename[:5])
            if len(cant_rename) > 5:
                name_str += ' ...'

            return u"无法清理 {} 个带命名空间的节点：\n{}".format(len(cant_rename), name_str)

        return ""

    except Exception:
        return traceback.format_exc()


def is_under_assembly_reference(node):
    """检查节点是否位于 assemblyReference 层级下面。"""
    try:
        current = node

        while True:
            parents = cmds.listRelatives(current, parent=True, fullPath=True) or []
            if not parents:
                break

            current = parents[0]

            if cmds.nodeType(current) == 'assemblyReference':
                return True

    except Exception:
        pass

    return False


def delete_unused_shaders(node, logger=None):
    """删除带命名空间且没有 dagSetMembers 连接的无用 ShadingEngine。"""
    default_sgs = {"initialParticleSE", "initialShadingGroup"}

    try:
        if cmds.nodeType(node) != 'shadingEngine':
            return False
    except Exception:
        return False

    short_name = node.split('|')[-1]

    if short_name in default_sgs:
        return False

    conns = cmds.listConnections(node + ".dagSetMembers", source=True, destination=False) or []
    if conns:
        return False

    try:
        materials = cmds.listConnections(node + ".surfaceShader", source=True, destination=False) or []
        delete_nodes = [node]

        for material in materials:
            connected_sgs = cmds.listConnections(material, type='shadingEngine') or []
            connected_sgs = list(set(connected_sgs))

            if len(connected_sgs) <= 1:
                delete_nodes.append(material)

        for item in delete_nodes:
            if cmds.objExists(item):
                cmds.lockNode(item, lock=False)

        delete_nodes = [item for item in delete_nodes if cmds.objExists(item)]

        if delete_nodes:
            cmds.delete(delete_nodes)

        if logger:
            logger.warning(u"AUTO FIX: 删除无用材质 {}".format(', '.join(delete_nodes)))

        return True

    except Exception as e:
        if logger:
            logger.warning(u"删除无用材质失败 {}: {}".format(node, e))

        return False