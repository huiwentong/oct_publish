# -*- coding: utf-8 -*-
import traceback

import maya.cmds as cmds
import maya.utils as utils


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    检查镜头相机的属性：Fit Resolution Gate / Overscan / shakeEnabled / 胶片尺寸 / 缩放 / 锁定
    """
    # 镜头相机的这些属性必须固定成项目规范值并锁定，避免各环节渲染取景不一致。
    try:
        def check():
            if not cmds.objExists('|cam'):
                return u"没有 |cam 组"

            error_cams = []
            for cam in cmds.listRelatives('|cam', ad=True, type='camera', fullPath=True) or []:
                cam_p = cmds.listRelatives(cam, p=True, fullPath=True)[0]
                reasons = []
                if cmds.getAttr(cam + '.filmFit') != 1:
                    reasons.append('filmFit 不是 Horizontal')
                if cmds.getAttr(cam + '.shakeEnabled'):
                    reasons.append('shakeEnabled 已开启')
                if any(round(s, 6) != 1 for s in cmds.getAttr(cam_p + '.scale')[0]):
                    reasons.append('相机有缩放')
                if (cmds.getAttr(cam + '.horizontalFilmAperture') != 0.980
                        or cmds.getAttr(cam + '.verticalFilmAperture') != 0.735):
                    reasons.append('胶片尺寸不是 0.980 x 0.735')
                if not cmds.getAttr(cam_p + '.rx', lock=True):
                    reasons.append('相机 transform 没有锁定')
                if reasons:
                    error_cams.append(u"{0}: {1}".format(cam_p, u'，'.join(reasons)))

            if error_cams:
                return u"相机属性检查未通过，请点击 Fix 修复：\n" + '\n'.join(error_cams)
            return ""

        result = utils.executeInMainThreadWithResult(check)
        if result:
            return result
    except:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """把 cam 组下所有相机的属性设为规范值并锁定 transform"""
    try:
        def repair():
            if not cmds.objExists('|cam'):
                return u"没有 |cam 组，无法修复"
            for cam in cmds.listRelatives('|cam', ad=True, type='camera', fullPath=True) or []:
                cam_p = cmds.listRelatives(cam, p=True, fullPath=True)[0]
                cmds.setAttr(cam + '.filmFit', 1)
                cmds.setAttr(cam + '.shakeEnabled', False)
                cmds.setAttr(cam + '.horizontalFilmAperture', lock=False)
                cmds.setAttr(cam + '.verticalFilmAperture', lock=False)
                cmds.setAttr(cam + '.horizontalFilmAperture', 0.980, lock=True)
                cmds.setAttr(cam + '.verticalFilmAperture', 0.735, lock=True)
                # 相机缩放不影响取景，修复时把缩放归一再锁定
                for attr in ['sx', 'sy', 'sz']:
                    plug = '{0}.{1}'.format(cam_p, attr)
                    if round(cmds.getAttr(plug), 6) != 1:
                        cmds.setAttr(plug, lock=False)
                        cmds.setAttr(plug, 1)
                        logger.warning(u"AUTO FIX: 相机 {0} 的 {1} 归一".format(cam_p, attr))
                for attr in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz']:
                    cmds.setAttr('{0}.{1}'.format(cam_p, attr), lock=True)
                logger.info(u"AUTO FIX: 相机属性已修复 {0}".format(cam_p))
            return ""

        return utils.executeInMainThreadWithResult(repair)
    except:
        return traceback.format_exc()
