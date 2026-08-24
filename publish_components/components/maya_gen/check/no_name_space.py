# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.cmds as cmds
import maya.utils as utils

def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
    检查并清理 非 Reference 节点命名空间
    """
    try:

        def delete_unused_shaders(node):
            default_sgs = {"initialParticleSE", "initialShadingGroup"}
            if node.type() == 'shadingEngine':
                if node.name() not in default_sgs:
                    conns = cmds.listConnections(node.name() + ".dagSetMembers", source=True, destination=False)
                    if not conns:
                        try:
                            materials = cmds.listConnections(node.name() + ".surfaceShader") or []
                            for i in [node.name()] + materials:
                                cmds.lockNode(i, lock=False)
                            cmds.delete([node.name()] + materials)
                            print('delete unused materials:')
                            print([node.name()] + materials)
                            return True
                        except Exception as e:
                            print("failed delete", node.name(), e)
            return False

        need_fix_nodes = []
        need_fix_node_names = []
        for obj in utils.executeInMainThreadWithResult(lambda : cmds.ls(allPaths=True, long=True)):
            try:
                n = pm.PyNode(obj)
            except:
                continue

            if n.isReferenced():
                continue

            if n.nodeType() in ['reference']:
                continue

            is_ref = False
            try:
                for p in pm.listRelatives(n, allParents=True):
                    if p.nodeType() == 'assemblyReference':
                        is_ref = True
            except:
                pass

            if is_ref:
                continue

            if ':' in n.nodeName():
                if delete_unused_shaders(n): continue
                need_fix_nodes.append(n)
                need_fix_node_names.append(n.longName())

        if len(need_fix_node_names) > 0:
            name_str = ', '.join(need_fix_node_names)
            logger.error(u"AUTO FIX: 发现 {} 个带命名空间的节点：\n{} \n尝试自动修复： ".format(len(need_fix_node_names), name_str))
            for fix_n in need_fix_nodes:
                try:
                    cmds.lockNode(fix_n.nodeName(), lock=False)
                    fix_n.rename(fix_n.nodeName().split(':')[-1])
                    logger.warning("AUTO FIX: 修复节点 {}".format(fix_n.nodeName()))
                except:
                    return "修复节点{}失败， 因为 {}".format(fix_n.nodeName(), traceback.format_exc())
    except:
        return traceback.format_exc()


