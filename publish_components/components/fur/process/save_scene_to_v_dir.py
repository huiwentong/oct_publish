# -*- coding: utf-8 -*-
import traceback, os
import pymel.core as pm
import maya.utils as utils

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """另存场景 ma 到版本文件夹。"""
    try:
        v_dir_ma_file = process_data.get("v_dir_ma_file")
        if not v_dir_ma_file:
            raise RuntimeError(u"没有获取到 v_dir_ma_file")
        v_dir_ma_file = v_dir_ma_file.replace("\\","/")
        new_workspace = os.path.dirname(v_dir_ma_file)
        utils.executeInMainThreadWithResult(lambda :pm.saveAs(v_dir_ma_file, force=True))
        utils.executeInMainThreadWithResult(lambda :pm.workspace(new_workspace, openWorkspace=True))

        if logger:
            logger.info(u"场景保存完成：{}".format(v_dir_ma_file))
    except Exception:
        return traceback.format_exc()