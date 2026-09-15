# -*- coding: utf-8 -*-
import traceback

import maya.cmds as cmds
import maya.utils as utils

from oct.pipeline.task_context import TaskContext


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    检查镜头中 reference 的路径是否为正确的资产发布路径
    """
    # 引用必须来自 I:/projects/<项目>/asset 下，且不能引用带版本号的绑定文件（要用无版本号目录）。
    # 项目名从任务上下文取而不是 OCT_PROJECT 环境变量，CLI 模式下没有环境变量也能跑。
    try:
        tc = TaskContext(process_data['task_id'])
        proj_name = tc.project_name.lower()

        def check():
            l_error_refs = []
            for ref in cmds.file(q=True, r=True) or []:
                rfn = cmds.file(ref, q=True, rfn=True)
                if cmds.file(rfn=rfn, q=True, deferReference=True):
                    continue
                if not ref.lower().startswith("i:/projects/{0}/asset".format(proj_name)):
                    l_error_refs.append([rfn, ref])
                    continue
                version_name = ref.split("/")[-2]
                if len(version_name.split('.')) > 3:  # ref 带版本号的绑定文件
                    l_error_refs.append([rfn, ref])
            return l_error_refs

        l_error_refs = utils.executeInMainThreadWithResult(check)
        if l_error_refs:
            return u'文件中存在非正确资产路径的引用: \n' + \
                   '\n'.join('{0}: {1}'.format(rfn, ref) for rfn, ref in l_error_refs)
    except:
        return traceback.format_exc()
