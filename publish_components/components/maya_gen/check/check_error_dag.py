# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.utils as utils

def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
    检查层级下是否存在非 transform,mesh,instancer 以外的节点类型
    """
    try:
        def check():
            l_error_nodes = list()
            high_node = process_data.get('high', '|Root_grp|Geo_grp|high')
            for node in pm.listRelatives(high_node, ad=1):
                if node.nodeType() not in ['transform', 'mesh', 'camera', 'instancer']:
                    l_error_nodes.append(node.name())
            return l_error_nodes

        error_nodes = utils.executeInMainThreadWithResult(check)
        if error_nodes:
            return u"大纲层级下存在非 transform,mesh,instancer 以外的节点类型，节点列表如下：{}".format('\n'.join(error_nodes))
    except:
        return traceback.format_exc()


