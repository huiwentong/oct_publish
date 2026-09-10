# -*- coding: utf-8 -*-
import traceback
import maya.utils as utils
from oct.pipeline.task_context import TaskContext
from publish_components.utils.maya_utils import asb_build

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查新版 ASB Stage 是否存在未保存的 USD 修改"""
    try:
        tc = TaskContext(process_data['task_id'])
        def check():
            root, legacy, proxies = asb_build.scene_info(tc.entity_name)
            return [] if legacy else asb_build.dirty_proxies(proxies)
        dirty = utils.executeInMainThreadWithResult(check)
        process_data['asb_dirty_proxies'] = dirty
        if dirty:
            return '以下 USD 文件未保存:\n' + '\n'.join(dirty)
    except Exception:
        return traceback.format_exc()

def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """保存新版 ASB Stage 的 root layer"""
    try:
        tc = TaskContext(process_data['task_id'])
        def repair():
            root, legacy, proxies = asb_build.scene_info(tc.entity_name)
            if not legacy:
                asb_build.save_usd_roots(proxies)
                if asb_build.dirty_proxies(proxies):
                    raise RuntimeError('USD 保存后仍有未保存修改')
        utils.executeInMainThreadWithResult(repair)
    except Exception:
        return traceback.format_exc()
