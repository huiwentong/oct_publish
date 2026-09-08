# -*- coding:utf-8 -*-
import traceback
import pymel.core as pm
import maya.utils as utils

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    保存场景
    """
    try:
        def process():
            pm.saveFile(force=True)
        utils.executeInMainThreadWithResult(process)
    except:
        return traceback.format_exc()

