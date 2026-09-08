# -*- coding: utf-8 -*-
import traceback, os
import subprocess
from oct.pipeline.task_context import TaskContext
def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """提交deadline任务: Turntable"""

    try:
        task_id = process_data.get("task_id")
        tc = TaskContext(task_id) or TaskContext.from_env()

        def submit_to_deadline_turntable():
            proj_name = tc.project_name.lower()
            asset_name = tc.entity_name
            dept = tc.step.short_name.lower()
            task = tc.task_name
            env_dict = os.environ
            env_dict['REZ_CONFIG_FILE'] = r'\\192.168.15.15\pipeline\config\rezconfig.py'
            cmd = ["rez-env",
                   "oct_turntable_to_deadline",
                   "--",
                   "tt_to_deadline",
                   str(proj_name),
                   str(asset_name),
                   str(dept),
                   str(task)
                   ]
            subprocess.run(cmd, check=True, env=env_dict, creationflags=subprocess.CREATE_NO_WINDOW)
            logger.debug('run submitTurntableToDeadline args: {} {} {} {}'.format(proj_name, asset_name, dept, task))

        if tc.entity.sg_asset_type.lower() in ["chr", "ch", "prop", "prp"]:
            submit_to_deadline_turntable()

    except Exception:
        return traceback.format_exc()
