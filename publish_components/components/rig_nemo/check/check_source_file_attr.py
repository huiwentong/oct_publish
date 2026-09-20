#!/usr/bin/env python  
# -*- coding:utf-8 -*-

import traceback
import os
import re

import maya.cmds as mc
import maya.utils as utils
from oct_maya.utils.path import parse_context_file_path


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
检查源文件属性
    """
    try:
        def process():
            if mc.objExists('Root_grp.riggingPath'):
                source_file = mc.getAttr('Root_grp.riggingPath')
                context_info = parse_context_file_path(source_file)

                if not (context_info and source_file.startswith('I:/projects')):
                    return u'这个NemoRig不是从Publish版本的绑定制作发布的!'

                process_data[u'源文件'] = source_file

        result = utils.executeInMainThreadWithResult(process)
        if result:
            return result

    except:
        return traceback.format_exc()
