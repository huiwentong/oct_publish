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
        # def find_max_version(parent_dir, pattern=r"v(\d+)"):
        #     """
        #     非递归遍历 parent_dir，找到所有文件名中包含 v<数字> 的最大版本号。
        #     例如：gouyao.rig.rigging.v011 -> 11
        #     """
        #     max_version = None
        #
        #     for entry in os.listdir(parent_dir):
        #         match = re.search(pattern, entry)
        #         if match:
        #             version = int(match.group(1))
        #             if max_version is None or version > max_version:
        #                 max_version = version
        #
        #     return max_version
        #
        # def get_previous_version_path(file_path):
        #     parent_dir = os.path.dirname(file_path)
        #     file_name = os.path.basename(file_path)
        #
        #     # 从当前文件名中提取当前版本号
        #     current_match = re.search(r"v(\d+)", file_name)
        #     if not current_match:
        #         raise ValueError(f"路径中未找到版本号：{file_path}")
        #
        #     current_version = int(current_match.group(1))
        #
        #     # 非递归遍历父目录，查找已存在的最大版本号
        #     max_version = find_max_version(parent_dir)
        #
        #     if max_version is None:
        #         raise ValueError(f"父目录中未找到任何版本号：{parent_dir}")
        #
        #     # 如果当前版本已经是最大版本，则减 1
        #     if current_version == max_version:
        #         new_version = current_version - 1
        #     else:
        #         # 如果当前版本不是最大版本，说明可能存在缺失版本，
        #         # 这里仍然按“减少 1”处理
        #         new_version = current_version - 1
        #
        #     if new_version < 0:
        #         raise ValueError(f"版本号减 1 后小于 0：{file_path}")
        #
        #     # 保持原版本号位数，例如 v011 -> v010
        #     digit_len = len(current_match.group(1))
        #     new_version_str = f"v{new_version:0{digit_len}d}"
        #
        #     new_file_name = re.sub(r"v\d+", new_version_str, file_name, count=1)
        #     new_file_path = os.path.join(parent_dir, new_file_name)
        #
        #     return new_file_path
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

# def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
#     try:
#         def process():
#             pass
#
#         return utils.executeInMainThreadWithResult(process)
#     except:
#         return traceback.format_exc()
