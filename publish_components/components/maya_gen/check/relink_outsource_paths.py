# -*- coding: utf-8 -*-
import traceback, os
import pymel.core as pm
from oct.pipeline.task_context import TaskContext
from publish_components.utils.gen_func import is_outsourcing
from publish_components.utils.maya_utils.maya_path_relinker import execute_relinker

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """替换外包贴图路径"""
    try:
        work_file = (submit_data.get("ma_file") or '').replace('\\', '/')
        is_outsource = process_data.get("is_outsourcing", is_outsourcing(work_file))
        if not parent_widget and is_outsource:
            task_id = process_data['task_id']
            tc = TaskContext(task_id) or TaskContext.from_env()
            next_version_name = tc.task.next_version()
            output_name = "{}.ma".format(next_version_name)
            new_maya_file, log = execute_relinker(work_file, os.path.dirname(work_file), output_name)

            if "auto_description" not in process_data:
                process_data["auto_description"] = {}
            process_data["auto_description"].update({'outsourcing root': os.path.dirname(work_file)})
            process_data.update({'version_num': next_version_name.split(".")[-1],
                                 'dcc_file': str(new_maya_file)})
            submit_data.update({"ma_file": str(new_maya_file)})
            pm.openFile(new_maya_file, f=True)
    except Exception:
        return traceback.format_exc()
