# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm

def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
    检查重命名的节点, 在 high + blendshape 组下所有节点的命名是唯一的。
    """
    try:

        n_geo = process_data.get("geo", '|Root_grp|Geo_grp')
        n_high = process_data.get("high", '|Root_grp|Geo_grp|high')
        d_names = {}

        node_list = pm.listRelatives(n_high, ad=True)
        if pm.objExists(n_geo.fullPath() + '|blendshape'):
            n_bs = pm.PyNode(n_geo.fullPath() + '|blendshape')
            node_list.append(n_bs)
            node_list.extend(pm.listRelatives(n_bs, ad=True))

        for node in node_list:
            n_name = node.nodeName()
            if n_name not in d_names:
                d_names[n_name] = []

            d_names[n_name].append(node)

        l_existing_names = list(d_names.keys())
        for n_name, l_nodes in d_names.items():
            l_paths = list(set([n.fullPath() for n in l_nodes]))
            if len(l_nodes) > 1:
                logger.warning("名字为 ’{}‘ 的物体有：{}".format(n_name, ",".join(l_paths)))
                for n in l_nodes:
                    logger.warning("AUTO FIX: 开始自动修复节点：{}".format(n.fullPath()))
                    i = 1
                    while n.nodeName() in l_existing_names:
                        tokens = n_name.split('_')
                        if len(tokens) > 1:
                            tokens.insert(-1, str(i))
                        else:
                            tokens.append(str(i))
                        new_name = '_'.join(tokens)
                        if new_name in l_existing_names:
                            i += 1
                        else:
                            n.rename(new_name)
                    l_existing_names.append(n.nodeName())
    except:
        return traceback.format_exc()


