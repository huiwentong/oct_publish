#!/usr/bin/env python  
# -*- coding:utf-8 -*-

import traceback
from publish_core.database.entity import FastSg, SGEntity
import maya.cmds as mc
import maya.utils as utils


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
更新shotgun版本, 添加备注
    """
    try:
        def process():
            if mc.objExists('Root_grp.cocoVersion'):
                coco_v = mc.getAttr('Root_grp.cocoVersion')
                sg = FastSg().client
                task_id = process_data.get('task_id', '')
                sg.update('Version', task_id, {'client_code': coco_v})

            return None

        result = utils.executeInMainThreadWithResult(process)
        if result:
            return result

    except:
        return traceback.format_exc()
