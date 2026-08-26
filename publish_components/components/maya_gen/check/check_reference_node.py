# -*- coding: utf-8 -*-

import traceback
import os


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    def run_check():
        import pymel.core as pm
        global pm
        try:
            l_errs = []
            l_ref = pm.ls(type='reference')
            if len(l_ref):
                for ref_node in l_ref:
                    l_errs.append(u'{};'.format(ref_node.name()))
                return u"当前文件中存在 Reference 节点：\n" + '\n'.join(l_errs)
            return ""

        except:
            return traceback.format_exc()

    def run_fix():
        import maya.cmds as cmds
        rfs = cmds.file(q=1,r=1)
        for rf in rfs:
            cmds.file(rf,rr=1)

        return ""

    check_result = run_check()
    if check_result:
        run_fix()

