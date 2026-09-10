# -*- coding: utf-8 -*-
import traceback
import maya.utils as utils
from oct.pipeline.task_context import TaskContext
from publish_components.utils.maya_utils import asb_build

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查新版 Stage 使用 maya_usd/工程版本名.usda 相对路径"""
    try:
        tc = TaskContext(process_data['task_id'])
        def check():
            root, legacy, proxies = asb_build.scene_info(tc.entity_name)
            return [] if legacy else asb_build.proxy_paths(proxies, submit_data['ma_file'])
        paths = utils.executeInMainThreadWithResult(check)
        process_data['asb_usd_relative_paths'] = paths
    except Exception:
        return traceback.format_exc()
