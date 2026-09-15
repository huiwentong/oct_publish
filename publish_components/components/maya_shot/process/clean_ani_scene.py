# -*- coding: utf-8 -*-
import traceback

import maya.utils as utils

from oct_maya.utils.maya_utils.pipe import rename_deformed_shape


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    清理动画文件：修正异常命名的 deformed shape
    """

    try:
        utils.executeInMainThreadWithResult(rename_deformed_shape)
    except:
        return traceback.format_exc()
