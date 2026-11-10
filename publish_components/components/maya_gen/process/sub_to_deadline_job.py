# -*- coding: utf-8 -*-
import traceback, os
import subprocess
import maya.utils as utils
from oct.pipeline.task_context import TaskContext
from oct_maya.tools.utils.oct_asset_turntable.core.api import TurntableAPI
from publish_components.utils.sg_helper import get_asset_kind, MAYA_SCENE_TAG, UE_SCENE_TAG

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """提交deadline任务: Turntable"""

    try:
        task_id = process_data.get("task_id")
        tc = TaskContext(task_id) or TaskContext.from_env()
        ordered_files = process_data.get('ordered_files')

        def submit_to_deadline_turntable():
            proj_name = tc.project_name.lower()
            asset_name = tc.entity_name
            dept = tc.step.short_name.lower()
            if dept == "mod":
                version_dir = process_data.get("version_dir")
                output_dir = version_dir + '/preview/origin'
                tt_api = TurntableAPI()
                info = utils.executeInMainThreadWithResult(lambda :tt_api.render_all_cameras(output_dir=output_dir, step=dept, data=None,
                                                            asset_name=asset_name, template_key="TT_3points", remove_template=True))
                result = info.get("message")
                logger.info(result)

            else:
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

        # Maya场景 / UE场景资产不做 turntable
        is_scene_asset = get_asset_kind(task_id) in (MAYA_SCENE_TAG, UE_SCENE_TAG)

        if not ordered_files and not is_scene_asset and tc.entity.sg_asset_type.lower() in ["chr", "ch", "prop", "prp"]:
            submit_to_deadline_turntable()

    except Exception:
        return traceback.format_exc()
