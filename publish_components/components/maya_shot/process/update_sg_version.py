# -*- coding: utf-8 -*-
import os
import traceback

from oct.pipeline.shotgun.config import API_SCRIPTS
from oct.pipeline.shotgun.models import Asset, PublishedFile, Shot, Version
from oct.pipeline.task_context import TaskContext


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    更新 SG Version 字段: 添加 PublishedFile、帧范围, Submit / Publish 时更新镜头的资产链接和 cut 范围
    """
    # Dailies 只登记预览 PublishedFile；
    # Submit / Publish 再登记 ma / shot_components / comp_transform，写 Version 帧范围，
    # 并把 shot_comp_data 里的资产链接到镜头上。
    #
    # 注意：此组件会创建 PublishedFile 并修改 Version / Shot 字段。
    #
    # 本组件在 Dailies 模式下也会跑，而 Dailies 允许在 Maya 外提交（独立 GUI / CLI 的 cmd 模式），
    # 组件的 import 会被提到 CLI 脚本最前面，所以这里不能导入 maya.*；
    # 文件帧范围由 check_file_frame_range 在 Maya 里读好写进 process_data['frame_range']。
    try:
        Version.use_script(API_SCRIPTS.version_up_tool)
        tc = TaskContext(process_data['task_id'])
        version_ref = process_data['sg_version']
        version = Version.get(id=version_ref['id'])
        if version.sg_task.id != tc.task_id or version.code != process_data['version_name']:
            raise RuntimeError(u'待更新的 SG Version 与本次任务/版本不一致')

        entity = {'type': tc.entity_type, 'id': tc.entity_id}
        task = {'type': 'Task', 'id': tc.task_id}
        project = {'type': 'Project', 'id': tc.project_id}
        version_number = version.version_number

        def create_published_file(code, path):
            PublishedFile.create(code=code,
                                 path={'local_path': path.replace('/', '\\')},
                                 path_cache=path,
                                 name=code,
                                 version={'type': 'Version', 'id': version.id},
                                 version_number=version_number,
                                 entity=entity,
                                 task=task,
                                 project=project,
                                 sg_component=None,
                                 sg_component_version=None)
            logger.info(u"创建 PublishedFile {0}: {1}".format(code, path))

        version_dir = process_data['version_dir']
        version_name = process_data['version_name']
        v_dir_preview = process_data.get('v_dir_preview') or ''
        if os.path.exists(v_dir_preview):
            create_published_file(os.path.basename(v_dir_preview), v_dir_preview)

        if process_data.get('publish_type') in ('Submit', 'Publish'):
            v_dir_ma_file = process_data.get('v_dir_ma_file') or ''
            if os.path.exists(v_dir_ma_file):
                create_published_file(os.path.basename(v_dir_ma_file), v_dir_ma_file)

            shot_comp_file = os.path.join(version_dir, 'shot_components.json').replace('\\', '/')
            if os.path.exists(shot_comp_file):
                create_published_file(version_name + '.shot_components', shot_comp_file)

            comp_trans_file = os.path.join(version_dir, 'data', 'comp_transform.json').replace('\\', '/')
            if os.path.exists(comp_trans_file):
                create_published_file(version_name + '.comp_transform', comp_trans_file)

            frame_range = process_data.get('frame_range')
            if not frame_range:
                raise RuntimeError(u'process_data 里没有 frame_range，请确认 check_file_frame_range 已运行')
            start_f, end_f = int(frame_range[0]), int(frame_range[1])
            version.frame_range = '({0}, {1})'.format(start_f, end_f)
            version.save()

            # 镜头的资产链接：拆分任务不覆盖已有链接，只追加
            asset_list = []
            if submit_data.get('is_split_task'):
                shot = Shot.get(id=tc.entity_id, fields=['assets'])
                asset_list = [a if isinstance(a, dict) else a.to_dict() for a in (shot.assets or [])]
            linked_names = set(a.get('name') for a in asset_list if a.get('name'))

            shot_comp_data = process_data.get('shot_comp_data') or {}
            asset_names = sorted(set(info['asset_name'] for info in shot_comp_data.values())
                                 - linked_names)
            if asset_names:
                for asset in Asset.filter(filters=[['project', 'is', project], ['code', 'in', asset_names]],
                                          fields=['code']):
                    asset_list.append({'type': 'Asset', 'id': asset.id, 'name': asset.code})

            shot = Shot.get(id=tc.entity_id, fields=['id'])
            shot.assets = asset_list
            shot.sg_cut_in = start_f
            shot.sg_cut_out = end_f
            shot.save()
            logger.info(u"镜头 {0} 链接 {1} 个资产，cut 范围 {2}-{3}".format(
                tc.entity_name, len(asset_list), start_f, end_f))
    except:
        return traceback.format_exc()
