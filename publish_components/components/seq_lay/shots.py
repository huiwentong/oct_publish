# -*- coding: utf-8 -*-
"""
扫描场次文件里的镜头，GUI 镜头表格和 check_shot_versions 共用
"""
import glob
import os

import maya.cmds as cmds

from oct.pipeline.path_acs import old_get_path
from oct.pipeline.shotgun.models import Task


def scan_scene_shots():
    """场景里的 <code>_shot 节点 -> [(code, start_f, end_f)]，只读 Maya，需在主线程调用"""
    shots = []
    for node in cmds.ls(type='shot') or []:
        if node.endswith('_shot'):
            shots.append((node[:-len('_shot')],
                          int(cmds.getAttr(node + '.startFrame')),
                          int(cmds.getAttr(node + '.endFrame'))))
    return shots


def query_shots(project_name, scene_shots):
    """
    按镜头 code 到 SG 上找 rough_layout 任务和工作目录下最新的拍屏。
    找不到任务的镜头 task_id 为 None，由调用方决定怎么处理。
    """
    # ponytail: 每个镜头单独查一次 SG，一个场次几十个镜头够用；慢了再改成一次 'in' 查询
    shots = []
    for code, start_f, end_f in scene_shots:
        info = {'shot': code, 'start_f': start_f, 'end_f': end_f,
                'task_id': None, 'sg_ani_cut_in': None, 'sg_ani_cut_out': None,
                'work_dir': '', 'preview': ''}
        tasks = Task.filter(project_name=project_name,
                            filters=[['entity.Shot.code', 'is', code],
                                     ['content', 'is', 'rough_layout'],
                                     ['sg_status_list', 'is_not', 'omt']])
        if tasks:
            task = tasks[0]
            work_dir = old_get_path(mount_point='work', show_name=project_name,
                                    entity_type='Task', id=task.id, key='maya').replace('\\', '/')
            movs = sorted(glob.glob(work_dir + '/*.v???.mov'),
                          key=lambda p: int(os.path.basename(p).split('.')[-2][1:]))
            info.update({'task_id': task.id,
                         'sg_ani_cut_in': task.entity.sg_ani_cut_in,
                         'sg_ani_cut_out': task.entity.sg_ani_cut_out,
                         'work_dir': work_dir,
                         'preview': movs[-1].replace('\\', '/') if movs else ''})
        shots.append(info)
    return shots
