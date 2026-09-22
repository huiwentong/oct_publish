# -*- coding: utf-8 -*-
import traceback
import maya.utils as utils
import pymel.core as pm
from oct.pipeline.task_context import TaskContext
from publish_components.utils.maya_utils import asb_build

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查 ASB 根组及当前场景，初始化组装数据"""
    # 表单文件与当前场景是否一致由 maya_shot/check_picked_file_is_current 负责
    try:
        tc = TaskContext(process_data['task_id'])
        def check():
            root, legacy, proxies = asb_build.scene_info(tc.entity_name)
            return pm.PyNode(root), legacy, proxies
        root, legacy, proxies = utils.executeInMainThreadWithResult(check)
        process_data.update(root=root, asb_legacy=legacy, asb_proxy_shapes=proxies,
                            entity_name=tc.entity_name, high=None, low=None)
    except Exception:
        return traceback.format_exc()
