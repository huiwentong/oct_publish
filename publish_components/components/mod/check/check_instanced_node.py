# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm

def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
    检查最高组之下是否有关联复制的节点。如果出现，自动转成普通节点
    """
    try:
        def convert_instance_to_object(n1):
            n_name = n1.nodeName()
            n2 = pm.duplicate(n1)[0]
            pm.delete(n1)
            n2.rename(n_name)
        n_root = process_data.get('root', '|Root_grp')
        l_instanced = []
        l_nodes = pm.listRelatives(n_root, ad=True)
        for node in l_nodes:
            l_parents = pm.listRelatives(node, allParents=True)
            if len(l_parents) > 1:
                l_instanced.extend(l_parents)

        if len(l_instanced) > 0:
            for n in l_instanced:
                try:
                    logger.warning("AUTO FIX: 修复关联复制的物体 {}".format(n.nodeName()))
                    convert_instance_to_object(n)
                except:
                    return "修复节点{}失败， 因为 {}".format(n.nodeName(), traceback.format_exc())

    except:
        return traceback.format_exc()


