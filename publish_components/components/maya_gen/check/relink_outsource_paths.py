# -*- coding: utf-8 -*-
import traceback, os
import pymel.core as pm
from publish_components.utils.gen_func import is_outsourcing
from publish_components.utils.maya_utils.maya_path_relinker import execute_relinker

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """替换外包贴图路径"""
    try:
        work_file = (submit_data.get("ma_file") or '').replace('\\', '/')
        if not parent_widget and is_outsourcing(work_file):
            execute_relinker(work_file, os.path.dirname(work_file))
            pm.openFile(work_file, f=True)
    except Exception:
        return traceback.format_exc()
