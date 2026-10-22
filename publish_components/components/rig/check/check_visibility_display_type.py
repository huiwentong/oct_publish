#!/usr/bin/env python
# -*- coding:utf-8 -*-

import traceback
import pymel.core as pm
import maya.utils as utils


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
Visibility 的 displayType 通道是否连接模型的显示属性
    """
    try:
        process_data['vis_dsp_typ_setting'] = {
            'Visibility.displayType': 2,
            'Geo_grp.overrideDisplayType': 2,
            'Geo_grp.overrideEnabled': 1,
        }

        def process():
            error_list = []
            for k, v in process_data['vis_dsp_typ_setting'].items():
                if pm.objExists(k):
                    if pm.getAttr(k) != v:
                        error_list.append(k)

            if error_list:
                return u"以下节点设置错误：{}".format(', '.join(error_list))
            return ""

        result = utils.executeInMainThreadWithResult(process)
        if result:
            return result



    except:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    try:
        def process():
            for itm in process_data['vis_dsp_typ_setting']:
                if pm.objExists(itm):
                    correct_v = process_data['vis_dsp_typ_setting'][itm]
                    if pm.getAttr(itm) != correct_v:
                        node = pm.PyNode(itm)
                        node.unlock()
                        pm.setAttr(itm, correct_v)
                else:
                    logger.info(u"未找到: {}".format(itm))

        return utils.executeInMainThreadWithResult(process)

    except:
        return traceback.format_exc()
