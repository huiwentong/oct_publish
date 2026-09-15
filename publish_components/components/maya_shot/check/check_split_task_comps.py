# coding=utf-8
import traceback

import maya.utils as utils

from oct.pipeline.shotgun.config import API_SCRIPTS
from oct.pipeline.shotgun.models import Task
from oct_maya.tools.lay.usd_lay_manager_new.core import export_usd_json


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None) -> str | None:
    """检查拆分任务与同镜头、同环节其他任务是否重复使用 component。"""
    try:
        # 普通任务不检查，但不能 return ''，否则会提前结束拼接后的 CLI。
        if submit_data.get('is_split_task', False):
            Task.use_script(API_SCRIPTS.Generic)
            current_task = Task.get(id=process_data['task_id'])
            scene_data = utils.executeInMainThreadWithResult(export_usd_json)
            scene_comps = {name for name, data in scene_data.items()
                           if not data['usd_path'].startswith('/world/asset/asb')
                           and '_cam' not in name}
            conflicts = []
            for task in current_task.entity.tasks:
                if task.id == current_task.id or task.step.id != current_task.step.id:
                    continue
                for comp in task.sg_components or []:
                    if 'cam' not in comp.name and comp.name in scene_comps:
                        conflicts.append('{0} ({1})'.format(comp.name, task.content))
            if conflicts:
                return '以下资产在其他拆分任务中重复出现:\n' + '\n'.join(sorted(set(conflicts)))
    except Exception:
        return traceback.format_exc()
