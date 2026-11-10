# -*- coding: utf-8 -*-
import os
import traceback

import maya.utils as utils
from oct.pipeline.path_acs import old_get_path
from oct.pipeline.task_context import TaskContext
from publish_core.database.entity import get_step_short_name
from oct_maya.utils.path import parse_context_file_path


def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
    检查文件名和文件路径是否符合规范。
    """
    # 这个模块之后重构可以与version up going 里的 auto save 合并
    try:
        def check():
            dcc = process_data.get("dcc")
            task_id = process_data.get("task_id")
            tc = TaskContext(task_id) or TaskContext.from_env()
            version_name = process_data.get("version_name")
            # parse_context_file_path 只认正斜杠；CLI 传进来的 Windows 路径可能是反斜杠
            work_file = (submit_data.get("ma_file") or '').replace('\\', '/')
            ext = work_file.split('.')[-1]
            try:
                context_info = parse_context_file_path(work_file)
            except IndexError:
                return u"路径解析失败，文件名要求：资产名.环节.任务名.版本号.ma，请通过 Oct-Tools 的 [打开文件] 来创建初始文件"
            is_right_path = False

            # 短名按老工具规则解析（description 优先）：绑定 -> rig，镜头 lay(ly) -> lay
            _temp_step_name = get_step_short_name(tc.step)
            _temp_version_name = version_name.replace("绑定", "rig")

            if context_info:
                if context_info['disk'] == 'W:':
                    if context_info['entity_code'] != tc.entity_name.lower():
                        return u"当前资产名称不规范，请确认大小写"
                    if context_info['proj'].lower() == tc.project_name.lower() and \
                            context_info['entity_type'] == tc.entity_type.lower() and \
                            context_info['entity_code'] == tc.entity_name.lower() and \
                            context_info['step'] == _temp_step_name and \
                            context_info['task'] == tc.task_name.lower():
                        is_right_path = True
            if not is_right_path:
                work_dir = old_get_path('work', show_name=tc.project_name.upper(),
                                        entity_type='Task', id=task_id)
                correct_path = '/'.join([work_dir.replace('\\', '/'), dcc.lower(), _temp_version_name + '.' + ext])
                return u"当前文件的路径和名称不符合规范，正确的文件应该是{}。".format(correct_path)

            work_file_name = os.path.basename(work_file)
            work_version_name = work_file_name.rsplit('.', 1)[0]
            if work_version_name != _temp_version_name:
                return u"工程文件名 {} 和版本名 {} 不一致".format(work_version_name, _temp_version_name)
            return None

        error_msg = utils.executeInMainThreadWithResult(check)
        if error_msg:
            return error_msg

    except:
        return traceback.format_exc()


