# -*- coding: utf-8 -*-
import traceback

import maya.cmds as cmds
import maya.utils as utils


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    检查 cam 组的 transform 不能有数值
    """
    # 老 proj_mk2_gen/check_cam_grp
    try:
        def check():
            if not cmds.objExists('|cam'):
                return u"没有 |cam 组"
            if len(cmds.ls('cam')) > 1:
                return u"cam 有重名"
            for attr in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz']:
                if round(cmds.getAttr('|cam.{0}'.format(attr)), 6) != 0:
                    return u"|cam 组的 transform 有数值，请点击 Fix 归零"
            return ""

        result = utils.executeInMainThreadWithResult(check)
        if result:
            return result
    except:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """把 cam 组的位移 / 旋转归零并锁定"""
    try:
        def repair():
            if not cmds.objExists('|cam'):
                return u"没有 |cam 组，无法修复"
            for attr in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz']:
                plug = '|cam.{0}'.format(attr)
                cmds.setAttr(plug, lock=False)
                cmds.setAttr(plug, 0)
                cmds.setAttr(plug, lock=True)
            logger.info(u"AUTO FIX: |cam 组 transform 已归零并锁定")
            return ""

        return utils.executeInMainThreadWithResult(repair)
    except:
        return traceback.format_exc()
