# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm

def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
    检查最高组之下是否有关联复制的节点。如果出现，自动转成普通节点
    """
    try:
        n_root = process_data.get('root', '|Root_grp')
        l_instanced = []
        l_nodes = pm.listRelatives(n_root, ad=True)
        for node in l_nodes:
            l_parents = pm.listRelatives(node, allParents=True)
            if len(l_parents) > 1:
                l_instanced.extend(l_parents)

        if len(l_instanced) > 0:
            process_data["check_instanced_node_error_nodes"] = l_instanced
            msg = "以下节点是关联复制的节点：\n{}".format("\n".join(l_instanced))
            return msg

    except:
        return traceback.format_exc()

def fix(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    try:
        failed_nodes = []
        error_nodes = process_data.get('check_instanced_node_error_nodes', [])
        for n in error_nodes:
            try:
                logger.warning("AUTO FIX: 修复关联复制的物体 {}".format(n.nodeName()))
                n_name = n.nodeName()
                n2 = pm.duplicate(n)[0]
                pm.delete(n)
                n2.rename(n_name)
            except:
                logger.error("修复节点{}失败， 因为 {}".format(n.nodeName(), traceback.format_exc()))
                failed_nodes.append(n.nodeName())
        if len(failed_nodes):
            msg = "这些关联复制的节点自动修复失败, 请手动修复！：{}".format("\n".join(failed_nodes))
            logger.error(msg)
            return msg
    except:
        return traceback.format_exc()

