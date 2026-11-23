import traceback
import os
import shutil
import traceback
import sys
import subprocess
from oct.pipeline.path_acs import lock_path, unlock_path, make_dirs
from publish_components.utils import images
from publish_core.database.entity import get_user, SGEntity
from publish_core.database.core import FastSg
import re

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
根据拆分的镜头表更改/创建镜头信息
    """
    try:
        sg = FastSg().client
        tc = SGEntity('Task', process_data['task_id'])
        seq = tc.entity.tiny_raw()

        project_name = process_data['project_name']
        project_entity = sg.find_one('Project', [['code', 'is', project_name.lower()],], ['id'])


        all_shots = []


        for _clip in submit_data['clip_data']:
            shot_name = _clip['clip_name']
            all_shots.append(shot_name)
            duration = _clip['duration']
            order = _clip['order']
            cut_in = _clip['rec_in']
            cut_out = _clip['rec_out']
            s_filter = [
                ['project', 'name_is', project_name.lower()],
                ['code', 'is', shot_name]
            ]
            shot = sg.find_one('Shot', s_filter, ['id'])
            shot_fields = {
                'sg_cut_in': cut_in,
                'sg_cut_out': cut_out,
                'sg_ani_cut_in': 101,
                'sg_ani_cut_out': 101+duration,
                'sg_cut_duration': duration,
                'sg_cut_order': order,
                'sg_status_list': 'ip',
            }
            if shot:
                # ---- 已存在：更新 ----
                sg.update('Shot', shot['id'], shot_fields)
                logger.info(f"更新 Shot: {shot_name} (id={shot['id']})")
            else:
                shot_data = {
                    'code': shot_name,
                    'project': project_entity,
                    'entity': seq,
                    **shot_fields,
                }
                shot_entity  = sg.create('Shot', shot_data)
                logger.info(f"创建 Shot: {shot_name}")
                task_data = {
                    'project': project_entity,
                    'entity': shot_entity,           
                    'content': 'editing',
                    'step': {'type': 'Step', 'id': 200},              
                }
                task_entity = sg.create('Task', task_data)
                logger.info(f"为 Shot {shot_name} 创建 editing 任务 (id={task_entity['id']})")
        logger.info(f"开始禁用掉不在拆分表中的镜头")
        for shot in tc.entity.shots:
            if shot.code not in all_shots:
                sg.update('Shot', shot.id, {'sg_status_list': 'omt'})
                logger.info(f"禁用 Shot: {shot.code} (id={shot.id})")
    except:
        return traceback.format_exc()