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
        dcc = process_data.get("dcc")
        widget = process_data.get("widget")
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
            #TODO 添加自动保存功能
            # if not dcc:
            #     return u"没有任何 dcc 中, 无法自动保存文件！"
            # if dcc == 'Maya':
            #     import pymel.core as pm
            #     from oct_maya.tools.pipe.oct_save_as import app_launcher as oct_save_as
            #     p = oct_save_as.OctLauncher("oct_save_as", "pipe", "command", dockable=False, enable_log=False,
            #                                 log_level="info", check_context=True, ui_style="")
            #     p.setup_launcher()
            #     p.launch()
            #     scene_path = pm.sceneName()
            #     if scene_path != '' and widget:
            #         tokens = os.path.basename(scene_path).split('.')
            #         p = re.compile('v\d\d\d')
            #         if p.match(tokens[-2].lower()):
            #             new_version_num = tokens[-2][1:]
            #             print("#"*100)
            #             print(new_version_num)
            #             widget._version_edit.setText(new_version_num)
            #             process_data.update({"version_num": new_version_num})
    except:
        return traceback.format_exc()


