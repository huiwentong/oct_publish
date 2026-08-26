# -*- coding: utf-8 -*-
import os
import re
import traceback
from oct.pipeline.task_context import TaskContext


def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
    检查版本(Version)号是否上升
    """
    # 版本名应该是独一无二的，并且版本号应该上升。比如之前最高版本为v015，则新版本最低应该是v016。"

    try:
        version_num = process_data.get("version_num")
        if not version_num:
            return u"没有获取到有效的版本号"
        task_id = process_data.get("task_id")
        tc = TaskContext(task_id) or TaskContext.from_env()
        tc.refresh()

        all_v_nums = []
        for v in tc.task.versions():
            v_name = str(v.code)
            v_num_str = v_name.replace('_', '.').split('.')[-1]
            if len(v_num_str) == 4 and v_num_str.lower()[0] == 'v' and v_num_str[1:].isdigit():
                all_v_nums.append(v_num_str)
        if len(all_v_nums) > 0 and version_num <= max(all_v_nums):
            logger.warning(u"之前已经提交了 {} 版, 新版本 {} 版本号不够高。将自动保存文件并增大版本号。".format(max(all_v_nums), version_num))
            return u"之前已经提交了 {} 版, 新版本 {} 版本号不够高。将自动保存文件并增大版本号。".format(max(all_v_nums), version_num)
    except:
        return traceback.format_exc()


