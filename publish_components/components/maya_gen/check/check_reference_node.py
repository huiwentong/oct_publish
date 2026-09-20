# -*- coding: utf-8 -*-

import traceback
import os
import pymel.core as pm
import maya.cmds as cmds
import maya.utils as utils


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
检查 Reference 节点是否存在
    """
    try:
        def process():
            l_errs = []
            l_ref = pm.ls(type='reference')
            if l_ref:
                for ref_node in l_ref:
                    l_errs.append(u'{};'.format(ref_node.name()))
                msg = u"当前文件中存在 Reference 节点：\n" + '\n'.join(l_errs)
                logger.warning(msg)
                return msg
            return ''

        result = utils.executeInMainThreadWithResult(process)
        if result:
            return result

    except:
        return traceback.format_exc()


def fix(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    try:
        def process():
            rfs = cmds.file(query=True, reference=True)
            logger.info(u"AUTO FIX: 删除 {0} 个Reference节点".format(len(rfs)))
            for rf in rfs:
                cmds.file(rf, rr=True)
        return utils.executeInMainThreadWithResult(process)
    except:
        return traceback.format_exc()