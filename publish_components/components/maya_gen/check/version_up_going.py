# -*- coding: utf-8 -*-
import os
import re
import traceback
import importlib

from oct.pipeline.task_context import TaskContext
from publish_core.database.entity import get_step_short_name


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查版本(Version)号是否上升"""
    try:
        def version_num_with_file(file_path):
            if not file_path:
                return None
            scene_v = int(file_path.split('.')[-2][1:])
            return 'v{:03d}'.format(scene_v)

        form_widget = process_data.get("widget")
        task_id = process_data.get("task_id")

        if form_widget:
            version_num = form_widget._version_edit.text()
        else:
            version_num = process_data.get("version_num")
            if not version_num:
                dcc_file = process_data.get("dcc_file") or ""
                version_num = version_num_with_file(dcc_file)

        if not version_num:
            return u"没有获取到有效的版本号"

        tc = TaskContext(task_id) or TaskContext.from_env()
        tc.refresh()

        all_v_nums = []
        for v in tc.task.versions():
            v_name = str(v.code)
            v_num_str = v_name.replace('_', '.').split('.')[-1]
            if len(v_num_str) == 4 and v_num_str.lower()[0] == 'v' and v_num_str[1:].isdigit():
                all_v_nums.append(v_num_str)

        if all_v_nums and version_num <= max(all_v_nums):
            return u"之前已经提交了 {} 版, 新版本 {} 版本号不够高".format(max(all_v_nums), version_num)

    except:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """自动修复版本号，并在 Maya 中保存为新版本"""

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
            if version > latest_version_num:
                latest_version_num = version
        return latest_version_num

    try:
        dcc = process_data.get("dcc")
        task_id = process_data.get("task_id")
        tc = TaskContext(task_id) or TaskContext.from_env()
        tc.refresh()

        form_widget = process_data.get("widget")

        if not dcc:
            msg = u"没有任何 dcc 中, 无法自动保存文件！"
            logger.error(msg)
            return msg

        if dcc == 'Maya':
            pm = importlib.import_module("pymel.core")
            mu = importlib.import_module("maya.utils")
            xgg = importlib.import_module("xgenm.xgGlobal")

            def save_as_scene(task_context):
                pm.saveAs(new_scene_file, f=True)
                pm.refresh(force=True)
                if get_step_short_name(task_context.step) == "fur":
                    xgg.DescriptionEditor.refresh('Full')
                logger.warning(u"AUTO FIX: 自动保存新版本：{}".format(new_scene_file))

            scene_path = pm.sceneName()
            if not scene_path:
                return u"当前 Maya 场景尚未保存，无法自动升版"

            scene_path = str(scene_path)
            scene_dir = os.path.dirname(scene_path)
            ext = scene_path.split('.')[-1]

            mu.executeInMainThreadWithResult(lambda: pm.saveFile(force=True))

            version_key = "{}.{}.{}".format(tc.entity_name, get_step_short_name(tc.step), tc.task_name)

            workspace_latest_v_num = get_latest_version_num(scene_dir, version_key,("ma", "mb"))
            workspace_next_v_num = workspace_latest_v_num + 1

            sg_next_version_name = tc.task.next_version()
            sg_next_version_num = int(sg_next_version_name.split('v')[-1])

            next_version_num = "v{:03d}".format(max(workspace_next_v_num, sg_next_version_num))

            new_scene_file = os.path.join(scene_dir, version_key + '.' + next_version_num + '.' + ext)
            new_scene_file = str(new_scene_file).replace("\\", "/")

            mu.executeInMainThreadWithResult(lambda: save_as_scene(tc))

            if form_widget:
                form_widget._version_edit.setText(next_version_num)

            process_data.update({"version_num": next_version_num, "dcc_file": new_scene_file})
            submit_data.update({"ma_file": new_scene_file})

    except:
        return traceback.format_exc()