#!/usr/bin/env python
# -*- coding:utf-8 -*-

import traceback
import pymel.core as pm
import maya.utils as utils
from publish_core.database.entity import FastSg, SGEntity
from oct.pipeline.task_context import TaskContext


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
检查 Nemo Rig 文件层级
    """
    try:
        def process():
            if not pm.objExists('|Root_grp'):
                return u"找不到最高层级的组 |Root_grp"

            if not pm.objExists('|Root_grp|Geo_grp'):
                return u"找不到保存面的组 |Root_grp|Geo_grp"

            task = SGEntity('Task', process_data['task_id'])
            version_dir = process_data.get("version_dir")
            sg = FastSg().client
            entity_name = task.entity.code
            a_filters = [
                ['code', 'is', entity_name],
                ['project', 'name_is', task.project.code],
            ]
            tc = TaskContext(process_data['task_id']) or TaskContext.from_env()

            sg_asset = sg.find_one(
                'Asset', filters=a_filters, fields=['code', 'sg_asset_type', 'sg_cname', 'shots', 'sg_status_list'])

            sg_task = process_data.get('task_entity')
            sg_task.update(
                {
                    "content": tc.task_name.lower(),
                    "step": {
                        "id": tc.step.id,
                        "name": tc.step_name,
                        "type": tc.step.type
                    },
                    "project": {
                        "id": tc.project_id,
                        "name": tc.project_name,
                        "type": tc.project.entity_type,
                        "code": tc.project_name
                    },
                    "sg_status_list": tc.task.sg_status_list
                }
            )

            process_data.update({
                'sg_asset': sg_asset,
                'sg_asset_type': tc.entity.sg_asset_type,
                'sg_task': sg_task,
                'root': pm.PyNode('|Root_grp'),
                'geo': pm.PyNode('|Root_grp|Geo_grp'),
                'high': None,
                'low': None,
                'v_dir': version_dir,
                'v_dir_tmp': version_dir,
            })

            return None

        result = utils.executeInMainThreadWithResult(process)
        if result:
            return result

    except:
        return traceback.format_exc()
