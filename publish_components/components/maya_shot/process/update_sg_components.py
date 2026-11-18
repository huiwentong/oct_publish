# -*- coding: utf-8 -*-
import os
import traceback

import maya.utils as utils

from oct.pipeline.shotgun.config import API_SCRIPTS
from oct.pipeline.shotgun.models import Version
from oct.pipeline.task_context import TaskContext
from oct_maya.tools.lay.usd_lay_manager_new.core import export_usd_json


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    把当前场景的 component 记录更新到 SG（Component / ComponentVersion）
    """
    # 每个场景 component 在当前任务下 get_or_create 一个 Component，
    # 再按本次版本号创建 ComponentVersion，记录 high.usd 缓存路径；
    # Bk / An 环节发布时同步给 rough_layout 任务也建一份 Component。
    #
    # 注意：此组件会创建 / 修改 SG 的 Component 与 ComponentVersion。
    try:
        Version.use_script(API_SCRIPTS.version_up_tool)
        tc = TaskContext(process_data['task_id'])
        version_ref = process_data['sg_version']
        sg_version = Version.get(id=version_ref['id'])
        if sg_version.code != process_data['version_name']:
            raise RuntimeError(u'待更新的 SG Version 与本次版本不一致')
        sg_task = sg_version.sg_task
        logger.info(u'current version id: {0}'.format(sg_version.id))

        comp_data = utils.executeInMainThreadWithResult(export_usd_json)

        # 写入 cache_usd 路径
        component_dir = os.path.join(sg_version.get_path(mount_point='publish'), 'component')
        for comp, data in comp_data.items():
            if data['visible'] is False or data['usd_path'].startswith('/world/asset/asb'):
                continue
            comp_data[comp]['cache_usd'] = os.path.join(component_dir, comp, 'high.usd').replace('\\', '/')

        # Bk / An 发布时，comps 同步给 rough_layout 任务
        sg_lay_task = None
        if tc.step_name in ['Bk', 'An']:
            # SG 的 Task 没有 code 字段，按 content 找 rough_layout 任务
            for t in sg_task.entity.tasks:
                if t.content == 'rough_layout':
                    sg_lay_task = t
                    logger.info(u'Find the rough_layout task, id: {0}'.format(sg_lay_task.id))
                    break

        for prim, comp_dict in comp_data.items():
            component = sg_task.get_or_create_component(name=prim)
            sg_task.link_component(component)
            logger.info(u'link Component({0}) to Task({1})'.format(component.id, sg_task.id))

            if sg_lay_task:
                for_lay_component = sg_lay_task.get_or_create_component(name=prim)
                sg_lay_task.link_component(for_lay_component)
                logger.info(u'link Component({0}) to Lay Task({1})'.format(for_lay_component.id, sg_lay_task.id))

            # 为 component 创建版本，版本号与当前文件版本一致
            component_v_name = prim + '.' + sg_version.code.rsplit('.', 1)[1]
            status, sg_version_component = component.get_or_create_component_version(name=component_v_name)
            sg_version_component.sg_master_version = sg_version
            sg_version_component.sg_task = sg_task.to_dict()
            sg_version_component.sg_exported_path = comp_dict.get('cache_usd', '')
            sg_version_component.save()
            logger.info(u'ComponentVersion {0} ({1}): {2}'.format(
                component_v_name, status, sg_version_component.sg_exported_path))
    except:
        return traceback.format_exc()
