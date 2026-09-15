# -*- coding: utf-8 -*-
import os
import traceback

import maya.utils as utils

from oct.pipeline.path_acs import lock_path, unlock_path
from publish_components.utils.maya_utils import ma_edit


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    编辑版本目录里的 ma 文件：清理 mayaUsd 新属性，usda 引用路径改到发布目录
    """
    # 版本 ma 不存在或改写失败只记 warning，不中断发布。
    try:
        ma_path = (process_data.get('v_dir_ma_file') or '').replace('\\', '/')
        if ma_path and os.path.isfile(ma_path):
            mayausd_version = utils.executeInMainThreadWithResult(ma_edit.get_mayausd_version)
            try:
                unlock_path(ma_path)
                changed, msg = ma_edit.clean_mayausd_attrs_from_ma(ma_path, mayausd_version)
                logger.info(msg)
                changed, msg = ma_edit.fix_maya_usd_path_drive(ma_path)
                logger.info(msg)
                lock_path(ma_path)
            except Exception:
                logger.warning(u"编辑版本 ma 文件失败: {0}\n{1}".format(ma_path, traceback.format_exc()))
        else:
            logger.warning(u"版本目录里没有 ma 文件，跳过编辑: {0}".format(ma_path))
    except:
        return traceback.format_exc()
