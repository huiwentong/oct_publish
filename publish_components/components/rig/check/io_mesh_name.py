# -*- coding:utf-8 -*-

import traceback
import pymel.core as pm
import maya.utils as utils

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
检查资产 high 组内 intermediate object mesh 节点名
    """
    try:
        def run_check():
            result = None
            l_bad_names = []
            n_high = process_data.get("high", "|Root_grp|Geo_grp|high")
            print("n_high: ", n_high)
            for n_mesh in pm.listRelatives(n_high, ad=True, type='mesh'):
                if n_mesh.isIntermediateObject():
                    trans_node = n_mesh.getParent()
                    trans_name = trans_node.nodeName()
                    print("n_mesh.nodeName(): ", n_mesh.nodeName())
                    if n_mesh.nodeName() == trans_name + 'Shape':
                        l_bad_names.append(n_mesh.nodeName())

            if len(l_bad_names) > 0:
                result = u'Intermediate Object mesh 节点名不能由 transform + Shape 构成的：' + ', '.join(l_bad_names)
                logger.warning(result)

            if result:
                rename_count = 0
                n_high = process_data.get("high", "|Root_grp|Geo_grp|high")
                for n_mesh in pm.listRelatives(n_high, ad=True, type='mesh'):
                    if n_mesh.isIntermediateObject():
                        trans_node = n_mesh.getParent()
                        trans_name = trans_node.nodeName()
                        if n_mesh.nodeName() == trans_name + 'Shape':
                            n_mesh.rename(trans_name + 'ShapeOrig')
                            rename_count += 1
                logger.info(u"AUTO FIX: 重命名了 {} 个节点".format(rename_count))

        utils.executeInMainThreadWithResult(run_check)

    except:
        return traceback.format_exc()
