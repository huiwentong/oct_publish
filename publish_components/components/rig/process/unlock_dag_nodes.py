#!/usr/bin/env python  
# -*- coding:utf-8 -*-

import traceback
import maya.cmds as mc
import maya.utils as utils


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
解锁资产的dag层级
    """
    try:
        def process():
            if mc.objExists('Root_grp'):
                mc.lockNode(mc.listRelatives('Root_grp', c=1, ad=1, fullPath=1), lock=0)

            return None

        result = utils.executeInMainThreadWithResult(process)
        if result:
            return result

    except:
        return traceback.format_exc()
