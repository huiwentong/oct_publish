#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
@Author  ：huiwentong
@EMAIL   ：wentong.hui@pearlstudio.com
@Date    ：2024/7/23 14:42 
'''

import traceback
import hou
from oct_hou.utils.hou_utils.analysis_TC import find_all_installed_hdas



def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
publish的工程中不能包含本地私有的hda，否则其他人在打开工程或者引用工程时会出错
    """
    try:
        hdas = find_all_installed_hdas()
        root = hou.node("/obj")
        for n in root.allSubChildren():
            definition = n.type().definition()
            if not definition:
                continue
            logger.info(definition)
            if definition in hdas.values():
                return "当前工程中有用到公共环境中不存在的私有hda，请确保publish的工程没有这些hda！\n私有hda节点：{}".format(
                    n.path())

    except:
        return traceback.format_exc()
