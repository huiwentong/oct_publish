# -*- coding: utf-8 -*-
import json
import os
import traceback

import maya.utils as utils

from oct.pipeline.shotgun.errors import DoesNotExist
from oct.pipeline.shotgun.models import Asset, Tag, Task
from oct.pipeline.task_context import TaskContext

from publish_components.utils.maya_utils import get_asb_nodes


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    在SG上创建所有拆分后的资产，记录到gen_asset.json文件
    """
    # ！！本组件会往 ShotGrid 写数据，重跑前请留意 ！！
    #   1. 为每个拆分出来的层级创建 Asset（已存在则复用），并打上「ASB自动拆分」标签
    #   2. 为每个资产创建 model 任务（已存在则复用）
    #   3. 覆盖式更新每个 ASB 资产的 assets 字段（子资产 + ENV 占位）
    # 创建部分是幂等的，重跑不会产生重复资产；第 3 步是覆盖写，
    # 所以 ENV 占位必须和子资产一起提交，否则会把已有的关联清掉。
    #
    # 依赖 check_assembly_all_hierarchy 写入的 gen_asset_data，
    # 并把 id / model_task_id 回写进去，供 gen_asb_deadline_job 使用。
    try:
        # 辅助函数必须定义在 main() 内 —— CLI 模式下只有 import 和 main() 的函数体
        # 会被抽进生成脚本，模块级的函数会全部丢失
        def get_tag_or_create(tag_name):
            try:
                sg_tag = Tag.get(filters=[['name', 'is', tag_name]])
            except DoesNotExist:
                sg_tag = Tag.create(name=tag_name)
                logger.info(u"创建标签: {0} (id={1})".format(tag_name, sg_tag.id))
            return sg_tag

        def get_asset_or_create(asset_name, asset_type, project, user):
            if asset_type not in ('ASB', 'PROP'):
                raise RuntimeError(u"资产 {0} 的拆分类型不支持: {1}".format(asset_name, asset_type))
            filters = [
                ['code', 'is', asset_name],
                ['project', 'is', project],
            ]
            # 写入前再次核对所有同名记录，防止检查后标记或 SG 数据发生变化。
            existing_assets = Asset.filter(filters=filters)
            for existing in existing_assets:
                if existing.sg_asset_type != asset_type:
                    raise RuntimeError(
                        u"资产 {0} 类型冲突: SG类型={1}, 本次标记={2}，禁止创建同名资产".format(
                            asset_name, existing.sg_asset_type, asset_type))
            if len(existing_assets) > 1:
                raise RuntimeError(u"SG 中存在多个同名资产 {0}，请先处理重复记录".format(asset_name))
            if existing_assets:
                sg_asset = existing_assets[0]
                logger.info(u"资产已存在: {0} (id={1})".format(asset_name, sg_asset.id))
            else:
                sg_asset = Asset.create(
                    project=project,
                    code=asset_name,
                    sg_asset_type=asset_type,
                    sg_status_list='ip',
                    created_by=user,
                )
                logger.info(u"创建资产: {0} (id={1})".format(asset_name, sg_asset.id))

            # 打上「ASB自动拆分」标签，便于之后检索这批自动生成的资产
            sg_tag = get_tag_or_create(tag_name='ASB自动拆分')
            tags_list = sg_asset.tags[:]
            if sg_tag not in tags_list:
                tags_list.append(sg_tag)
                sg_asset.tags = tags_list
                sg_asset.save()

            return sg_asset

        def get_model_task_or_create(sg_asset, user):
            for task in sg_asset.tasks:
                if task.code == 'model':
                    logger.info(u"model 任务已存在: {0} (id={1})".format(
                        sg_asset.code, task.id))
                    return task

            sg_task = Task.create(
                project={'type': 'Project', 'id': sg_asset.project.id},
                content='model',
                entity={'type': 'Asset', 'id': sg_asset.id},
                step={'type': 'Step', 'id': 14},
                created_by=user,
            )
            logger.info(u"创建 model 任务: {0} (id={1})".format(sg_asset.code, sg_task.id))
            return sg_task

        tc = TaskContext(process_data['task_id']) or TaskContext.from_env()
        version_dir = process_data["version_dir"]
        gen_asset_data = process_data["gen_asset_data"]
        root = process_data["root"]
        user = process_data["user"]
        project = {'type': 'Project', 'id': tc.project_id}

        # 创建所有子资产（ASB 和 PROP）及其 model 任务
        for asset_name, asset_info in gen_asset_data.items():
            sg_asset = get_asset_or_create(asset_name=asset_name,
                                           asset_type=asset_info['asset_type'],
                                           project=project,
                                           user=user)
            sg_task = get_model_task_or_create(sg_asset=sg_asset, user=user)

            gen_asset_data[asset_name]['id'] = sg_asset.id
            gen_asset_data[asset_name]['model_task_id'] = sg_task.id

        # ENV 占位不建资产，但要和拆分出来的子资产一起 link 到父 ASB 上，
        # 否则下面覆盖式的 assets 更新会把 ENV 的关联关系清掉。
        # 读节点 notes 要走主线程
        env_placeholders = utils.executeInMainThreadWithResult(
            lambda: get_asb_nodes.get_env_placeholders(
                root_longname=root.longName(),
                project_name=tc.project_name))

        # 更新所有 ASB 的 assets 字段，link 到对应的 PROP
        for asset_name, asset_info in gen_asset_data.items():
            if asset_info['asset_type'] != 'ASB':
                continue

            sub_assets_entity_list = [
                {'id': gen_asset_data[name.split('|')[-1]]['id'],
                 'name': name.split('|')[-1],
                 'type': 'Asset'}
                for name in asset_info['sub_assets']
            ]

            for env_asset in env_placeholders.get(asset_info['longname'], []):
                if not env_asset['asset_id']:
                    logger.warning(u"ENV占位 {0} 没有记录资产id，不做关联".format(
                        env_asset['longname']))
                    continue
                sub_assets_entity_list.append({'id': env_asset['asset_id'],
                                               'name': env_asset['asset_name'],
                                               'type': 'Asset'})

            sg_asset = Asset.get(id=asset_info['id'])
            sg_asset.assets = sub_assets_entity_list
            sg_asset.save()
            logger.info(u"{0} 关联了 {1} 个子资产".format(
                asset_name, len(sub_assets_entity_list)))

        # 写入 gen_asset.json，农场端任务和事后排查都会读它
        json_file = os.path.join(version_dir, 'gen_asset.json')
        with open(json_file, 'w') as f:
            json.dump(gen_asset_data, f, indent=4)

        logger.info(u"已在 SG 上创建/复用 {0} 个资产，记录写入 {1}".format(
            len(gen_asset_data), json_file))

    except:
        return traceback.format_exc()
