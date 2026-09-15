# -*- coding: utf-8 -*-
import traceback

import maya.cmds as cmds
import maya.utils as utils


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    检查 usd 流程的 ref 层级关系：资产的 Root_grp 必须在 |World 下
    """
    # 不允许通过 reference 在 |World 外添加资产，否则缓存输出时找不到。
    try:
        def check():
            if not cmds.objExists('|World'):
                return u"当前文件没有 World 组"
            l_errs = [root for root in cmds.ls('*:Root_grp', long=True) if '|World' not in root]
            if l_errs:
                return u"当前文件中存在错误 reference（不在 |World 下）：\n" + '\n'.join(l_errs)
            return ""

        result = utils.executeInMainThreadWithResult(check)
        if result:
            return result
    except:
        return traceback.format_exc()
