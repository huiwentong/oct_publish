# -*- coding: utf-8 -*-
import os
import re
import traceback
import pymel.core as pm
import maya.utils as utils
from oct.pipeline.task_context import TaskContext


def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
    检查版本(Version)号是否上升
    """
    # 版本名应该是独一无二的，并且版本号应该上升。比如之前最高版本为v015，则新版本最低应该是v016。"
    # 如果加了 auto save 功能，配置工具时，把这个模块放在 version_name之前！！！
    def get_latest_version_num(folder: str, pattern: str, extensions: tuple[str, ...]):
        """获取指定目录中符合命名规则的最高版本号"""

        ext_pattern = "|".join(re.escape(ext.lstrip(".")) for ext in extensions)
        regex = re.compile(
            rf"^{re.escape(pattern)}\."
            rf"v(?P<version>\d{{3}})\."
            rf"(?P<ext>{ext_pattern})$",
            re.IGNORECASE,
        )

        latest_version_num = 1

        for filename in os.listdir(folder):
            match = regex.fullmatch(filename)
            if not match:
                continue
            version = int(match.group("version"))

            if latest_version_num is None or version > latest_version_num:
                latest_version_num = version

        return latest_version_num

    def version_num_with_file(file):
        if file != '':
            scene_v = int(file.split('.')[-2][1:])
            v_number = 'v{:03d}'.format(scene_v)
            return v_number
        return None

    try:
        task_id = process_data.get("task_id")
        form_widget = process_data.get("widget")
        tc = TaskContext(task_id) or TaskContext.from_env()
        tc.refresh()

        if form_widget:
            version_num = form_widget._version_edit.text()
        else:
            dcc_file = process_data["dcc_file"]
            version_num = process_data.get("version_num", version_num_with_file(dcc_file))

        if not version_num:
            return u"没有获取到有效的版本号"

        all_v_nums = []
        for v in tc.task.versions():
            v_name = str(v.code)
            v_num_str = v_name.replace('_', '.').split('.')[-1]
            if len(v_num_str) == 4 and v_num_str.lower()[0] == 'v' and v_num_str[1:].isdigit():
                all_v_nums.append(v_num_str)
        if len(all_v_nums) > 0 and version_num <= max(all_v_nums):
            logger.warning(u"之前已经提交了 {} 版, 新版本 {} 版本号不够高。将自动保存文件并增大版本号。"
                           u"".format(max(all_v_nums), version_num))
            scene_path = pm.sceneName()
            scene_dir = os.path.dirname(scene_path)
            ext = scene_path.split('.')[-1]
            if scene_path != '' and form_widget:
                    utils.executeInMainThreadWithResult(lambda :pm.saveFile(force=True))
                    version_key = "{}.{}.{}".format(tc.entity_name, tc.step_name, tc.task_name)
                    # 工作文件夹下，下一个版本号
                    workspace_latest_v_num = get_latest_version_num(scene_dir, version_key, ("ma", "mb"))
                    workspace_next_v_num = workspace_latest_v_num + 1
                    # shotgun 上面， 下一个版本号
                    sg_next_version_name = tc.task.next_version()
                    sg_next_version_num = int(sg_next_version_name.split('v')[-1])
                    next_version_num = f"v{max(workspace_next_v_num, sg_next_version_num):03d}"
                    new_scene_file = os.path.join(scene_dir, version_key + '.' + next_version_num + '.' + ext)
                    new_scene_file = str(new_scene_file).replace("\\", "/")
                    logger.warning(u"AUTO FIX: 自动保存新版本：{}".format(new_scene_file))
                    utils.executeInMainThreadWithResult(lambda :pm.saveAs(new_scene_file, f=True))
                    utils.executeInMainThreadWithResult(lambda :pm.refresh(force=True))
                    form_widget._version_edit.setText(next_version_num)
                    process_data.update({"version_num": next_version_num,
                                         "dcc_file": new_scene_file})
                    submit_data.update({"ma_file": new_scene_file})
    except:
        return traceback.format_exc()


