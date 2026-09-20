# -*- coding: utf-8 -*-

import os
import traceback
import maya.cmds as cmds
import maya.utils as utils


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    检查root_jnt下的所有骨骼的属性不可锁定
    """
    try:
        def process():
            if cmds.objExists('root_jnt'):
                bad_jnts = []
                jnts = cmds.listRelatives('root_jnt', ad=1, type='joint', f=1) or []
                jnts.append(u'root_jnt')
                for jnt in jnts:
                    for attr in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz']:
                        if cmds.getAttr(jnt + '.' + attr, l=1):
                            if jnt not in bad_jnts:
                                bad_jnts.append(jnt)
                if bad_jnts:
                    return u"root骨骼下有骨骼属性被锁定:{}".format(bad_jnts)

        result = utils.executeInMainThreadWithResult(process)
        if result:
            return result

    except:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    try:
        logger.info(u"AUTO FIX: 解除 root_jnt 下所有骨骼的属性锁定")
        def process():
            if cmds.objExists('root_jnt'):
                jnts = cmds.listRelatives('root_jnt', ad=1, type='joint', f=1) or []
                jnts.append(u'root_jnt')
                for jnt in jnts:
                    for attr in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz']:
                        cmds.setAttr(jnt + '.' + attr, k=1, l=0)

        return utils.executeInMainThreadWithResult(process)

    except:
        return traceback.format_exc()
