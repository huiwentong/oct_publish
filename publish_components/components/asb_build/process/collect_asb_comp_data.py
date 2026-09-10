# -*- coding: utf-8 -*-
import traceback
import maya.utils as utils
from oct.pipeline.task_context import TaskContext
from publish_components.utils.maya_utils import asb_build

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """收集 ASB 子资产引用、变换及可见性覆盖"""
    try:
        tc = TaskContext(process_data['task_id'])
        components = utils.executeInMainThreadWithResult(
            lambda: asb_build.collect_components(tc.entity_name))
        process_data['asb_components'] = components
        logger.info('已收集 {0} 个 ASB Component'.format(len(components)))
    except Exception:
        return traceback.format_exc()
