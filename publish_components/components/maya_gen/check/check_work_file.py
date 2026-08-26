# -*- coding: utf-8 -*-
import os
import traceback
from oct.pipeline.path_acs import old_get_path
from oct.pipeline.task_context import TaskContext
from oct_maya.utils.path import parse_context_file_path
def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
    检查文件名和文件路径是否符合规范。
    """
    # 这个模块之后重构可以与version up going 里的 auto save 合并
    try:
        dcc = process_data.get("dcc")
        task_id = process_data.get("task_id")
        tc = TaskContext(task_id) or TaskContext.from_env()
        version_name = process_data.get("version_name")
        work_file = submit_data.get("ma_file")
        ext = work_file.split('.')[-1]
        context_info = parse_context_file_path(work_file)
        is_right_path = False

        # 针对 step_name 的 "绑定" 中文，做特殊处理：
        _temp_step_name = "rig" if tc.step_name == "绑定" else tc.step_name.lower()
        _temp_version_name = version_name.replace("绑定", "rig")

        if context_info:
            if context_info['disk'] == 'W:':
                if context_info['proj'].lower() == tc.project_name.lower() and \
                        context_info['entity_type'] == tc.entity_type.lower() and \
                        context_info['entity_code'] == tc.entity_name.lower() and \
                        context_info['step'] == _temp_step_name and \
                        context_info['task'] == tc.task_name.lower():
                    is_right_path = True
        if not is_right_path:
            work_dir = old_get_path('work', show_name=tc.project_name.upper(),
                                    entity_type='Task', id=task_id)
            correct_path = os.path.join(work_dir, dcc.lower(), _temp_version_name + '.' + ext)
            return u"当前文件的路径和名称不符合规范，正确的文件应该是{}。".format(correct_path)

        work_file_name = os.path.basename(work_file)
        if work_file_name.rsplit('.', 1)[0] != _temp_version_name:
            return u"工程文件名 {} 和版本名 {} 不一致".format(work_file_name, _temp_version_name)

    except:
        return traceback.format_exc()


