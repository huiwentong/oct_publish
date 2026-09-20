#!/usr/bin/env python  
# -*- coding:utf-8 -*-
import os
import traceback
import json
import maya.cmds as cmds
import maya.utils as utils
from nemo.filter import scene_collect


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
整理rig文件
    """
    try:
        def getRigInfo():
            allTrans = cmds.listRelatives("Rig_grp", ad=1, c=1, ni=1, type="transform", path=1)

            keyables = scene_collect.get_controllers("*")
            extras = set()
            for k in scene_collect.get_controllers("*"):
                extras.add(scene_collect.get_extra(k))

            rigInfo = {
                "keyable": {},
                "extra": {},
                "fixed": {}
            }
            for t in allTrans:
                if cmds.nodeType(t) not in ["transform", "joint"]:
                    continue
                defaultValues = {}
                for attr in scene_collect.list_channel_box(t):
                    if attr in ['translateX', 'translateY', 'translateZ', 'rotateX', 'rotateY', 'rotateZ', 'scaleX',
                                'scaleY',
                                'scaleZ']:
                        if cmds.listConnections(t + "." + attr[:-1], d=0, s=1):
                            continue
                    if cmds.listConnections(t + "." + attr, d=0, s=1):
                        continue
                    defaultValues[attr] = cmds.getAttr(t + "." + attr)
                if t in keyables:
                    rigInfo["keyable"][t] = defaultValues
                elif t in extras:
                    rigInfo["extra"][t] = defaultValues
                else:
                    rigInfo["fixed"][t] = defaultValues

            return rigInfo

        def export_ctrl_info(out_path):
            with open(out_path, 'w') as f:
                json.dump(getRigInfo(), f, ensure_ascii=True, indent=4)

        def process():
            version_dir = process_data.get('version_dir', '')
            out_path = os.path.join(version_dir, 'controller_data.json').replace('\\', '/')
            export_ctrl_info(out_path)

            return None

        result = utils.executeInMainThreadWithResult(process)
        if result:
            return result

    except:
        return traceback.format_exc()
