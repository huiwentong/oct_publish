# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.utils as utils

def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
    检查重命名的节点, 在 high + blendshape 组下所有节点的命名是唯一的。
    """
    try:

        def check():
            n_geo = process_data.get("geo", '|Root_grp|Geo_grp')
            n_high = process_data.get("high", '|Root_grp|Geo_grp|high')
            n_geo = pm.PyNode(n_geo)
            n_high = pm.PyNode(n_high)
            d_names = {}
            err_msg = ''
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

            for n_name, l_paths in d_names.items():
                l_paths = list(set(l_paths))
                if len(l_paths) > 1:
                    err_msg += u'物体重名: ' + ' '.join([i.fullPath() for i in l_paths]) + '\n'
            return err_msg, d_names

        error_msg, error_nodes = utils.executeInMainThreadWithResult(check)
        if error_msg != '':
            process_data["unique_name_error_nodes"] = error_nodes
            return error_msg

    except:
        return traceback.format_exc()

def fix(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
    检查重命名的节点, 在 high + blendshape 组下所有节点的命名是唯一的。
    """
    try:
        def _fix():
            error_nodes_info = process_data.get("unique_name_error_nodes", {})
            l_existing_names = list(error_nodes_info.keys())
            for n_name, l_nodes in error_nodes_info.items():
                if len(l_nodes) > 1:
                    for n in l_nodes:
                        logger.warning("AUTO FIX: 开始自动修复重命名节点：{}".format(n.fullPath()))
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

        utils.executeInMainThreadWithResult(_fix)
    except:
        return traceback.format_exc()
