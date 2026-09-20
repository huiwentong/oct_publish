#!/usr/bin/env python  
# -*- coding:utf-8 -*-

import os
import traceback
import maya.cmds as mc
import maya.mel as mel
import maya.utils as utils
from publish_core.database.entity import SGEntity
from oct_maya.utils.maya_utils.transform import lock_and_hide_channelBox_attrs
from publish_components.utils.sg_helper import check_is_internal_rig


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
整理rig文件
    """
    try:
        def process():
            if not mc.objExists('Rig_grp.internalRig'):
                mc.addAttr('Rig_grp', ln='internalRig', at='bool', keyable=False)
            mc.setAttr('Rig_grp.internalRig', lock=0)
            task_id = process_data.get("task_id")
            if process_data.get("is_internal_rig") is None:
                process_data.update({"is_internal_rig": check_is_internal_rig(task_id)})
            if process_data["is_internal_rig"]:
                mc.setAttr('Rig_grp.internalRig', True, lock=1)
            else:
                mc.setAttr('Rig_grp.internalRig', False, lock=1)

            vis_ctrl = 'Visibility_ctrl'
            task = SGEntity('Task', process_data['task_id'])
            entity_name = task.entity.code
            if mc.objExists(vis_ctrl):
                if not mc.objExists(vis_ctrl + '.assetName'):
                    mc.addAttr(vis_ctrl, ln='assetName', at='enum', en='{}:'.format(entity_name))
                    mc.setAttr(vis_ctrl + '.assetName', lock=0)
                else:
                    if mc.getAttr(vis_ctrl + '.assetName', asString=True) != entity_name:
                        mc.addAttr(vis_ctrl + '.assetName', e=1, en='{}:'.format(entity_name))
            lock_and_hide_channelBox_attrs('high')
            lock_and_hide_channelBox_attrs('Geo_grp')

            return None

        result = utils.executeInMainThreadWithResult(process)
        if result:
            return result

    except:
        return traceback.format_exc()
