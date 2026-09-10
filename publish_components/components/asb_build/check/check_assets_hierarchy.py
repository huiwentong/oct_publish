# -*- coding: utf-8 -*-
import os
import traceback
import maya.cmds as cmds
import maya.utils as utils
import pymel.core as pm
from oct.pipeline.task_context import TaskContext
from publish_components.utils.maya_utils import asb_build

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查 ASB 根组及当前场景，初始化组装数据"""
    try:
        tc = TaskContext(process_data['task_id'])
        def check():
            source = submit_data['ma_file']
            current = cmds.file(query=True, sceneName=True)
            if not current or os.path.normcase(os.path.abspath(current)) != os.path.normcase(os.path.abspath(source)):
                raise RuntimeError('当前打开的 Maya 场景与发布表单的工程文件不一致')
            root, legacy, proxies = asb_build.scene_info(tc.entity_name)
            return pm.PyNode(root), legacy, proxies
        root, legacy, proxies = utils.executeInMainThreadWithResult(check)
        process_data.update(root=root, asb_legacy=legacy, asb_proxy_shapes=proxies,
                            entity_name=tc.entity_name, high=None, low=None)
    except Exception:
        return traceback.format_exc()
