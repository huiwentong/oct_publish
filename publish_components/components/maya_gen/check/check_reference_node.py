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
        def run_check():
            l_errs = []
            l_ref = pm.ls(type='reference')
            if l_ref:
                for ref_node in l_ref:
                    l_errs.append(u'{};'.format(ref_node.name()))
                logger.warning(u"当前文件中存在 Reference 节点：\n" + '\n'.join(l_errs))

                rfs = cmds.file(query=True, reference=True)
                for rf in rfs:
                    cmds.file(rf, rr=True)
                logger.info("AUTO FIX: 删除了 {} 个Reference节点：".format(len(rfs)))

        utils.executeInMainThreadWithResult(run_check)

    except:
        return traceback.format_exc()
