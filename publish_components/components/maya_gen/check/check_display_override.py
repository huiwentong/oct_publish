#!/usr/bin/env python  
# -*- coding:utf-8 -*-
import traceback
import pymel.core as pm
import maya.utils as utils


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
检查high组下dag节点的overrideEnabled属性
    """
    try:
        def process():
            process_data['error_node_list'] = []
            n_high = process_data.get('high', '|Root_grp|Geo_grp|high')
            l_nodes = pm.listRelatives(n_high, ad=True)
            for node in l_nodes:
                if pm.objExists(node + '.overrideEnabled'):
                    override_enabled = pm.getAttr(node + '.overrideEnabled')
                    if override_enabled:
                        process_data['error_node_list'].append(node.name())

            if len(process_data['error_node_list']) > 0:
                return u'发现以下节点的overrideEnabled属性打开了: {}'.format(', '.join(process_data['error_node_list']))
            return None

        result = utils.executeInMainThreadWithResult(process)
        if result:
            return result

    except:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    try:
        logger.info(u"AUTO FIX: 修复 high 组下 dag 节点的 overrideEnabled 属性")

        def process():
            for node in process_data.get('error_node_list', []):
                pm.setAttr(node + '.overrideEnabled', l=0)
                pm.setAttr(node + '.overrideEnabled', False)

        return utils.executeInMainThreadWithResult(process)
    except:
        return traceback.format_exc()
