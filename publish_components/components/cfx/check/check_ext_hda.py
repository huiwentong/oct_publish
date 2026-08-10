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
        private_defs = set(hdas.values())
        for node in hou.node("/obj").allSubChildren():
            try:
                node_type = node.type()
                definition = node_type.definition()
                if not definition:
                    continue
                if definition in private_defs:
                    return "当前工程中有私有HDA:\n{}".format(node.path())

            except hou.ObjectWasDeleted:
                continue
            except Exception:
                continue
    except:
        return traceback.format_exc()
