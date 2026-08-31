# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.utils as utils
def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
    检查角色模型材质的reflectivity属性
    """
    try:
        error_mats = []
        white_list = ['M_eyeshell']
        for mat in utils.executeInMainThreadWithResult(lambda: pm.ls(materials=True)):
            if not mat.hasAttr('reflectivity'):
                continue
            if mat.name() in white_list:
                continue
            if mat.attr('reflectivity').get() != 0.0:
                error_mats.append(mat)
        if len(error_mats) > 0:
            msg = u"以下材质的reflectivity属性不为0: \n{}".format('\n'.join([i.name() for i in error_mats]))
            process_data['check_mod_reflectivity_attr_error_nodes'] = error_mats
            return msg
    except:
        return traceback.format_exc()

def fix(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    try:
        error_mats = process_data.get('check_mod_reflectivity_attr_error_nodes', [])
        for mat in error_mats:
            logger.warning("AUTO FIX: 设置材质球 '{}' 的reflectivity属性为0".format(mat.name()))
            mat.attr('reflectivity').set(0.0)
    except:
        return traceback.format_exc()
