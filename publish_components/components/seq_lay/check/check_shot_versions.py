# -*- coding: utf-8 -*-
import os
import traceback

import maya.utils as utils

from oct.pipeline.path_acs import old_get_path
from oct.pipeline.shotgun.models import Task
from publish_components.components.seq_lay.shots import query_shots, scan_scene_shots


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    确定要拆分发布的镜头，按各镜头 SG 上的下一个版本号生成发布路径，并检查镜头工作目录里没有同号文件
    """
    # 镜头来源：process_data['shots']（GUI 勾选 / CLI input_form 传入，只需 shot，可选 preview），
    # 为 None 时发场景里所有能在 SG 上找到 rough_layout 任务的镜头。
    # 镜头版本号不跟场次走，取各自 SG 上的下一个版本。
    # Deadline 会在镜头工作目录生成 {version_name}.ma / maya_usd/{version_name}.usda，
    # 已有同号文件会被覆盖，所以这里直接报错，不允许跳过。
    # 只查这两个：拍屏 mov 由 camera_sequencer_creator_2024 按场次版本号命名，和镜头版本号撞上也不会被覆盖。
    # 通过后写入 process_data['linked_task_info']，供后面的 seq_lay process 和 Deadline 提交使用。
    try:
        project_name = process_data['project_name']
        scene_shots = {s['shot']: s for s in query_shots(project_name, utils.executeInMainThreadWithResult(scan_scene_shots))}

        requested = process_data.get('shots')
        if requested is None:
            requested = [{'shot': name} for name, s in scene_shots.items() if s['task_id']]

        errors = []
        linked_task_info = {}
        for req in requested:
            name = req['shot']
            shot = scene_shots.get(name)
            if not shot:
                errors.append(u'{0}: 场景里没有 {0}_shot 节点'.format(name))
                continue
            if not shot['task_id']:
                errors.append(u'{0}: SG 上找不到 rough_layout 任务'.format(name))
                continue
            preview = req.get('preview') or shot['preview']
            if not os.path.isfile(preview):
                errors.append(u'{0}: 找不到拍屏 {1}'.format(name, preview))
                continue

            task_id = shot['task_id']
            version_name = Task.get(id=task_id).next_version()
            version_key = version_name.rsplit('.', 1)[0]
            publish_root = old_get_path(mount_point='publish', show_name=project_name,
                                        entity_type='Task', id=task_id).replace('\\', '/')
            version_dir = publish_root + '/' + version_name
            work_dir = shot['work_dir']

            if os.path.exists(version_dir):
                errors.append(u'{0}: 版本目录已存在 {1}'.format(name, version_dir))
            conflicts = [p for p in ('{0}/{1}.ma'.format(work_dir, version_name),
                                     '{0}/maya_usd/{1}.usda'.format(work_dir, version_name))
                         if os.path.exists(p)]
            if conflicts:
                errors.append(u'{0}: 工作目录已有 {1} 的文件，请先处理：\n    {2}'.format(
                    name, version_name, '\n    '.join(conflicts)))

            linked_task_info[name] = {
                'task_id': task_id,
                'version_name': version_name,
                'publish_root': publish_root,
                'version_dir': version_dir,
                'version_dir_no_num': publish_root + '/' + version_key,
                'work_dir': work_dir,
                'preview': preview,
                'v_preview': '{0}/preview/{1}.mov'.format(version_dir, version_name),
                'start_f': shot['start_f'],
                'end_f': shot['end_f'],
            }
            logger.info(u'{0} -> {1}'.format(name, version_name))

        if not requested:
            errors.append(u'没有选择要发布的镜头')
        if errors:
            return u'\n'.join(errors)
        process_data['linked_task_info'] = linked_task_info
    except:
        return traceback.format_exc()
