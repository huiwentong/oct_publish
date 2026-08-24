# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.utils as utils
def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
    检查角色模型材质的reflectivity属性
    """
    try:
        white_list = ['M_eyeshell']
        for mat in utils.executeInMainThreadWithResult(lambda: pm.ls(materials=True)):
            if not mat.hasAttr('reflectivity'):
                continue
            if mat.name() in white_list:
                continue
            if mat.attr('reflectivity').get() != 0.0:
                logger.warning("AUTO FIX: 设置材质球 '{}' 的reflectivity属性为0".format(mat.name()))
                mat.attr('reflectivity').set(0.0)
    except:
        return traceback.format_exc()


