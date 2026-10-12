#!/usr/bin/env python
# -*- coding:utf-8 -*-

import traceback
import maya.utils as utils
import maya.cmds as cmds


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    '''
检查控制器是否有动画帧
    '''
    try:
        def collect_all_possible_ctrls(exclude_crvs: list[str]):
            ctrl_list = []
            for crv in cmds.ls(type='nurbsCurve'):
                if not cmds.listConnections(crv, d=0):
                    trans = cmds.listRelatives(crv, p=1)[0]

                    if exclude_crvs:
                        if trans in exclude_crvs:
                            continue

                    is_ctrl = True
                    for attr in ['t', 'r', 's', 'tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz']:
                        if cmds.listConnections(trans + '.' + attr, d=0):
                            is_ctrl = False
                    if is_ctrl and trans not in ctrl_list:
                        ctrl_list.append(trans)
                    dynamic_attrs = cmds.listAttr(trans, userDefined=1)
                    if dynamic_attrs:
                        for attr in dynamic_attrs:
                            if cmds.listConnections(trans + '.' + attr, s=0) and trans not in ctrl_list:
                                ctrl_list.append(trans)
                                break
            return ctrl_list

        def check_has_anim_keys(ctrls):
            has_anim_keys_ctrl_list = []
            for ctrl in ctrls:
                if cmds.keyframe(ctrl, query=True, keyframeCount=True):
                    has_anim_keys_ctrl_list.append(ctrl)
            return has_anim_keys_ctrl_list

        def process():
            all_possible_ctrls = collect_all_possible_ctrls(exclude_crvs=['ctrlBox'])
            has_anim_keys_ctrl_list = check_has_anim_keys(all_possible_ctrls)
            if has_anim_keys_ctrl_list:
                process_data['anim_keys_error_list'] = has_anim_keys_ctrl_list
                return u"以下控制器上有动画帧： {}".format(', '.join(has_anim_keys_ctrl_list))

        result = utils.executeInMainThreadWithResult(process)
        if result:
            return result

    except:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    try:
        if process_data.get('anim_keys_error_list'):
            for ctrl in process_data['anim_keys_error_list']:
                cmds.cutKey(ctrl)
    except:
        return traceback.format_exc()
