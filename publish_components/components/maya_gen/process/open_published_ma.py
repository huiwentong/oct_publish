# -*- coding: utf-8 -*-
import traceback, os
import pymel.core as pm
import maya.utils as utils
from oct.pipeline.task_context import TaskContext

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """打开提交后的maya文件"""
    try:

        def process():
            task_id = process_data['task_id']
            tc = TaskContext(task_id) or TaskContext.from_env()
            last_version = tc.task.latest_version_by_types(["Submit", "Publish"])
            sg_path_to_geometry = last_version.sg_path_to_geometry
            if os.path.exists(sg_path_to_geometry):
                pm.openFile(sg_path_to_geometry, force=True)

        utils.executeInMainThreadWithResult(process)


    except Exception:
        return traceback.format_exc()
