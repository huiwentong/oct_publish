# -*- coding: utf-8 -*-
import traceback, os
import pymel.core as pm
from oct.pipeline.task_context import TaskContext
def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """文件内标注publish版本。"""

    try:
        task_id = process_data["task_id"]
        tc = TaskContext(task_id) or TaskContext.from_env()
        step_name = tc.step_name
        version_num = process_data["version_num"]
        v_dir_ma_file = process_data['v_dir_ma_file']
        n_root = process_data.get('root', '|Root_grp')

        pm.lockNode(n_root, lock=False)
        l_attrs = pm.listAttr(n_root)
        if not step_name + 'Version' in l_attrs:
            pm.addAttr(n_root, shortName=step_name + 'v', longName=step_name + 'Version', dt="string")
        if not step_name + 'Path' in l_attrs:
            pm.addAttr(n_root, shortName=step_name + 'p', longName=step_name + 'Path', dt="string")

        pm.setAttr(n_root + "." + step_name + "Version", version_num, type="string")
        pm.setAttr(n_root + "." + step_name + "Path", v_dir_ma_file, type="string")

    except Exception:
        return traceback.format_exc()
