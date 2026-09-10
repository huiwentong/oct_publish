# -*- coding: utf-8 -*-
import os
import traceback

import maya.utils as utils
import pymel.core as pm


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    导出原始的asb总文件
    """
    # 把 ASB 根层级整体导出成 source.ma，农场端的每个子资产任务都从这个文件出发
    try:
        version_dir = process_data["version_dir"]
        root = process_data["root"]

        def export():
            target_file = os.path.join(version_dir, 'source.ma')
            pm.select(root, r=True)
            pm.exportSelected(target_file,
                              force=True,
                              options="v=0;",
                              type="mayaAscii",
                              pr=True,
                              es=True)
            pm.select(cl=True)
            return target_file

        # 组件跑在后台线程，Maya API 必须调度回主线程
        target_file = utils.executeInMainThreadWithResult(export)
        logger.info(u"已导出 ASB 总文件: {0}".format(target_file))

    except:
        return traceback.format_exc()
