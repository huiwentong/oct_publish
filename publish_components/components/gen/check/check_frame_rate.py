# -*- coding: utf-8 -*-

import traceback
import maya.cmds as cmds

from publish_core.database.entity import SGEntity


MAYA_FPS_MAP = {
    'game': 15,
    'film': 24,
    'pal': 25,
    'ntsc': 30,
    'show': 48,
    'palf': 50,
    'ntscf': 60,
}


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查 Maya 场景帧率是否与项目帧率一致。"""
    try:
        project_id = process_data.get("project_id")
        if not project_id:
            task_id = process_data.get("task_id")
            if not task_id:
                return u"没有获取到 task_id 或 project_id"

            task = SGEntity("Task", task_id)
            project_id = task.project.id

        project = SGEntity("Project", project_id)
        project_fps = project.sg_fps

        maya_time_unit = cmds.currentUnit(query=True, time=True)
        maya_fps = MAYA_FPS_MAP.get(maya_time_unit)

        if maya_fps is None:
            if maya_time_unit.endswith("fps"):
                try:
                    maya_fps = float(maya_time_unit[:-3])
                except Exception:
                    pass

        if maya_fps is None:
            return u"无法识别 Maya 帧率单位：{}".format(maya_time_unit)

        if float(maya_fps) != float(project_fps):
            return u"Maya场景帧率为 {}fps，项目帧率为 {}fps".format(maya_fps, project_fps)

        if logger:
            logger.info(u"帧率检查通过：{}fps".format(maya_fps))

        return ""

    except Exception:
        return traceback.format_exc()