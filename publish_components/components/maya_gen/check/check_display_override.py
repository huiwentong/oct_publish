#!/usr/bin/env python  
# -*- coding:utf-8 -*-
import traceback
import pymel.core as pm
import maya.utils as utils

error_node_list = []


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
检查high组下dag节点的overrideEnabled属性
    """
    try:
        def process():
            global error_node_list
            error_node_list = []
            n_high = process_data.get('high', '|Root_grp|Geo_grp|high')
            l_nodes = pm.listRelatives(n_high, ad=True)
            for node in l_nodes:
                if pm.objExists(node + '.overrideEnabled'):
                    override_enabled = pm.getAttr(node + '.overrideEnabled')
                    if override_enabled:
                        error_node_list.append(node.name())

            if len(error_node_list) > 0:
                return u'发现以下节点的overrideEnabled属性打开了: {}'.format(', '.join(error_node_list))

            return ""

        def run_fix():
            logger.info(u"AUTO FIX")
            for node in error_node_list:
                pm.setAttr(node + '.overrideEnabled', l=0)
                pm.setAttr(node + '.overrideEnabled', False)
            return ''

        return utils.executeInMainThreadWithResult(process)

    except:
        return traceback.format_exc()
