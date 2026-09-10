# -*- coding: utf-8 -*-
import traceback

import maya.utils as utils
import pymel.core as pm


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    ASB清理场景，仅清除历史
    """
    # 与旧 mod/clean_history 保持一致，不删除集合、不创建 cluster、不修改法线。
    try:
        def clean_history():
            pm.select(all=True)
            try:
                pm.mel.eval('DeleteHistory;')
            finally:
                pm.select(cl=True)

        utils.executeInMainThreadWithResult(clean_history)
        logger.info(u"已清除 ASB 场景历史")

    except:
        return traceback.format_exc()
