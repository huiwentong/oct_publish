# -*- coding: utf-8 -*-
import traceback

import maya.cmds as cmds
import maya.utils as utils

from publish_core.database.entity import SGEntity


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    检查帧速率
    """
    # 检查场景帧速率是否符合项目在 SG 上登记的 sg_fps
    try:
        # 映射表必须定义在函数内 —— CLI 模式下只有 import 和 main() 函数体会被
        # 抽进生成脚本，模块级的常量和辅助函数都会丢失
        fps_map = {
            "game": 15,
            "film": 24,
            "pal": 25,
            "ntsc": 30,
            "show": 48,
            "palf": 50,
            "ntscf": 60,
        }

        # GUI 模式下 process_data 里没有 project_id，从 task_id 现查。
        # 这里用 SGEntity 而不是 TaskContext：ORM 的 Project 只带默认字段，
        # 且 Project.get() 的缓存查找先于 fields 生效，tc.project.sg_fps 取不到值
        task = SGEntity('Task', process_data['task_id'])
        sg_fps = int(task.project.sg_fps)

        # 组件跑在后台线程，Maya API 需调度回主线程
        cur_unit = utils.executeInMainThreadWithResult(
            lambda: cmds.currentUnit(query=True, time=True))
        if fps_map.get(cur_unit, 0) != sg_fps:
            return u"当前文件帧速率 {0} 不符合项目的帧速率 {1}fps".format(cur_unit, sg_fps)

    except:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    把场景帧速率改为项目在 SG 上登记的 sg_fps
    """
    try:
        task = SGEntity('Task', process_data['task_id'])
        sg_fps = int(task.project.sg_fps)

        cmds.currentUnit(time="{:d}fps".format(sg_fps))
        logger.warning(u"AUTO FIX: 帧速率已设为 {0}fps".format(sg_fps))

    except:
        return traceback.format_exc()
