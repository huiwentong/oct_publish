# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm

def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
    清理资产文件中的displayLayer, animationLayer, renderLayer, arnold节点等
    """
    try:
        pm.delete(pm.ls(type='displayLayer'))
        pm.delete(pm.ls(type='animLayer'))
        pm.delete(pm.ls(type='renderLayer'))
        pm.delete(pm.ls(type='shot'))
    except:
        return traceback.format_exc()

