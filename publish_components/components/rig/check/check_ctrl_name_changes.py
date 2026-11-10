#!/usr/bin/env python  
# -*- coding:utf-8 -*-
import os.path
import traceback
import json
import re
import maya.cmds as mc
import maya.utils as utils
from oct.pipeline.task_context import TaskContext
from publish_components.utils.maya_utils import dialogs


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
检查控制器名称，和上一版相比大小写有没有变化
    """
    try:
        def get_all_ctrls(only_ctrl_itself=False, full_path=False):
            ctrl_list = mc.ls('*_ctrl', long=full_path)
            ctrl_list.extend(mc.ls('*_CTL', long=full_path))
            if only_ctrl_itself:
                ctrl_list = [ctrl for ctrl in ctrl_list if
                             not ctrl.endswith('_pri_ctrl') and not ctrl.endswith('_sec_ctrl')]
            return ctrl_list

        def process():
            task_id = process_data.get("task_id")
            tc = TaskContext(task_id) or TaskContext.from_env()
            task_name = tc.task_name.lower()
            if task_name != 'rigging':
                logger.info("当前任务不是rigging，已跳过")
                return None

            version_dir = process_data.get('version_dir', '')
            non_v_dir = version_dir[0:-5]
            controller_data_path = os.path.join(non_v_dir, "controller_data.json")
            controller_data = {}
            with open(controller_data_path, "r") as f:
                controller_data = json.load(f)
            temp_ctrl = []
            for c_type, c_dicts in controller_data.items():
                temp_ctrl.extend(list(c_dicts.keys()))
            prev_ctrls = sorted(list(set(temp_ctrl)))
            curr_ctrls = get_all_ctrls()

            diff_list = []
            for cc in curr_ctrls:
                if cc in prev_ctrls:
                    continue

                for pc in prev_ctrls:
                    if cc.lower() == pc.lower():
                        diff_list.append({
                            "prev_ctrl": pc,
                            "curr_ctrl": cc,
                        })
            if diff_list:
                return '发现控制器大小写不一致，请确认：{}'.format(
                    ', '.join([d["prev_ctrl"] + ' -> ' + d["curr_ctrl"] for d in diff_list]))

            return None

        result = utils.executeInMainThreadWithResult(process)
        if result:
            if parent_widget:
                message = result + "\n请自行判断是否影响下游并修复。如果这些是允许的，请跳过该模块。"
                selected = dialogs.message_dialog("提示", message, ["跳过检查", "停止提交"], parent=parent_widget)
                if selected == "停止提交":
                    return message
            else:
                return result

    except:
        return traceback.format_exc()
