# -*- coding: utf-8 -*-
import traceback
import importlib
from publish_core.database.entity import SGEntity


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查 Maya 场景帧率是否与项目帧率一致。"""
    try:
        dcc = process_data.get("dcc")
        dcc_file = process_data.get("dcc_file") or ""
        is_maya = dcc == "Maya" or str(dcc_file).lower().endswith((".ma", ".mb"))

        if not is_maya:
            if logger:
                logger.info(u"当前没有 Maya 场景，跳过 Maya 帧率检查")
        else:
            cmds = importlib.import_module("maya.cmds")

            maya_fps_map = {
                "game": 15,
                "film": 24,
                "pal": 25,
                "ntsc": 30,
                "show": 48,
                "palf": 50,
                "ntscf": 60
            }

            project_id = process_data.get("project_id")
            if not project_id:
                task_id = process_data.get("task_id")
                if not task_id:
                    raise RuntimeError(u"没有获取到 task_id 或 project_id")

                task = SGEntity("Task", task_id)
                project_id = task.project.id

            project = SGEntity("Project", project_id)
            project_fps = project.sg_fps

            maya_time_unit = cmds.currentUnit(query=True, time=True)
            maya_fps = maya_fps_map.get(maya_time_unit)

            if maya_fps is None and maya_time_unit.endswith("fps"):
                try:
                    maya_fps = float(maya_time_unit[:-3])
                except Exception:
                    pass

            if maya_fps is None:
                raise RuntimeError(u"无法识别 Maya 帧率单位：{}".format(maya_time_unit))

            if float(maya_fps) != float(project_fps):
                raise RuntimeError(u"Maya场景帧率为 {}fps，项目帧率为 {}fps".format(maya_fps, project_fps))

            if logger:
                logger.info(u"帧率检查通过：{}fps".format(maya_fps))

    except Exception:
        return traceback.format_exc()