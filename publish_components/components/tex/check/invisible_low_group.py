# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.utils as utils
def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
    隐藏low组
    """
    try:
        def check():
            n_low = process_data.get('low', '|Root_grp|Geo_grp|low')
            n_low = pm.PyNode(n_low)
            if pm.objExists(n_low):
                logger.warning("AUTO FIX: 设置 low 组不可见！")
                n_low.setAttr("v", lock=False)
                n_low.visibility.set(False)

        utils.executeInMainThreadWithResult(check)

    except:
        return traceback.format_exc()


