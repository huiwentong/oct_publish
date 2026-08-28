#!/usr/bin/env python  
# -*- coding:utf-8 -*-

import traceback
import maya.cmds as mc
import maya.utils as utils


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
升级W盘文件版本
    """
    try:
        def process():
            work_file = submit_data.get('ma_file', '')
            version = work_file.split('.')[-2]
            version_num = int(version[1:])
            new_work_file = work_file.replace('.{}.'.format(version), '.v{:03d}.'.format(version_num + 1))
            mc.file(rename=new_work_file)
            mc.file(save=1, f=1)

        return utils.executeInMainThreadWithResult(process)
    except:
        return traceback.format_exc()
