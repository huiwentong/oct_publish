# -*- coding: utf-8 -*-
import traceback
import os
import subprocess

import maya.utils as utils
from oct.pipeline.task_context import TaskContext
from oct_maya.tools.utils.oct_asset_turntable.core.api import TurntableAPI
from publish_components.utils.sg_helper import (
    get_asset_kind,
    MAYA_SCENE_TAG,
    UE_SCENE_TAG,
)


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """提交 Deadline Turntable 任务，支持从发布界面指定 Frame Step。"""

    try:
        task_id = process_data.get("task_id")
        tc = TaskContext(task_id) or TaskContext.from_env()
        formated_mov_dic = process_data.get("formated_mov_dic")

        def get_turntable_frame_step():
            sources = (
                ("submit_data", submit_data),
                ("submit_data.input_form", submit_data.get("input_form") if isinstance(submit_data, dict) else None),
                ("process_data", process_data),
                ("process_data.input_form", process_data.get("input_form") if isinstance(process_data, dict) else None),
            )
            for source_name, data in sources:
                if not isinstance(data, dict):
                    continue
                value = data.get("turntable_frame_step")
                if value is None or value == "":
                    continue
                if isinstance(value, bool):
                    raise ValueError(
                        "turntable_frame_step must be an integer, not bool "
                        "(source={}, value={!r})".format(source_name, value)
                    )
                try:
                    step = int(value)
                except (TypeError, ValueError):
                    raise ValueError(
                        "Invalid turntable_frame_step from {}: {!r}".format(source_name, value)
                    )
                if not 1 <= step <= 200 or str(value).strip() != str(step):
                    # Do not silently truncate values like 2.5 to 2.
                    raise ValueError(
                        "turntable_frame_step must be an integer from 1 to 200: {!r} "
                        "(source={})".format(value, source_name)
                    )
                return step, source_name
            return 4, "default"

        def submit_to_deadline_turntable():
            proj_name = tc.project_name.lower()
            asset_name = tc.entity_name
            dept = tc.step.short_name.lower()

            if dept == "mod":
                # 保留原有 Mod TurntableAPI 流程，不通过 tt_to_deadline2。
                version_dir = process_data.get("version_dir")
                output_dir = version_dir + "/preview/origin"
                tt_api = TurntableAPI()
                info = utils.executeInMainThreadWithResult(
                    lambda: tt_api.render_all_cameras(
                        output_dir=output_dir,
                        step=dept,
                        data=None,
                        asset_name=asset_name,
                        template_key="TT_3points",
                        remove_template=True,
                    )
                )
                result = info.get("message")
                if logger:
                    logger.info(result)
            else:
                task = tc.task_name
                frame_step, step_source = get_turntable_frame_step()
                frame_start = 1
                frame_end = 200

                env_dict = os.environ.copy()
                env_dict["REZ_CONFIG_FILE"] = (
                    r"\\192.168.15.15\pipeline\config\rezconfig.py"
                )
                cmd = [
                    "rez-env",
                    "oct_turntable_to_deadline",
                    "--",
                    "tt_to_deadline2",
                    str(proj_name),
                    str(asset_name),
                    str(dept),
                    str(task),
                    "--frame-start", str(frame_start),
                    "--frame-end", str(frame_end),
                    "--frame-step", str(frame_step),
                ]

                if logger:
                    logger.info(
                        "[TT] Turntable frames: {}-{}x{} (source: {})".format(
                            frame_start, frame_end, frame_step, step_source
                        )
                    )
                    logger.info("[TT] Submit command: {}".format(" ".join(cmd)))
                    if step_source == "default":
                        logger.info(
                            "[TT WARN] turntable_frame_step not found in publish data; using default 4"
                        )

                subprocess.run(
                    cmd,
                    check=True,
                    env=env_dict,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )

                if logger:
                    logger.debug(
                        "run submitTurntableToDeadline args: {} {} {} {}, step={}".format(
                            proj_name, asset_name, dept, task, frame_step
                        )
                    )

        # Maya 场景 / UE 场景资产不做 Turntable。
        is_scene_asset = get_asset_kind(task_id) in (MAYA_SCENE_TAG, UE_SCENE_TAG)
        if (
            not formated_mov_dic
            and not is_scene_asset
            and tc.entity.sg_asset_type.lower() in ("chr", "ch", "prop", "prp")
        ):
            submit_to_deadline_turntable()

    except Exception:
        return traceback.format_exc()
