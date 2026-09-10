# -*- coding: utf-8 -*-
import traceback

import pymel.core as pm


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """农场拆分后清理未使用的材质和贴图"""
    try:
        pm.mel.MLdeleteUnused()
        logger.info(u"已清理未使用的材质和贴图")
    except Exception:
        return traceback.format_exc()
