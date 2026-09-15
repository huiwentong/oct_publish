# -*- coding: utf-8 -*-
import traceback

import maya.cmds as cmds
import maya.utils as utils


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    检查起始帧是否为 101
    """
    # lay / blk / ani 镜头文件的起始帧统一从 101 开始。
    try:
        start = utils.executeInMainThreadWithResult(
            lambda: cmds.playbackOptions(q=True, min=True))
        if int(start) != 101:
            return u"起始帧是 {0}，不是从 101 开始".format(int(start))
    except:
        return traceback.format_exc()
