# -*- coding: utf-8 -*-
import re
import traceback
from oct.pipeline.shotgun.models import Component, ComponentVersion
from oct.pipeline.shotgun.config import API_SCRIPTS
from oct.pipeline.task_context import TaskContext

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """创建 ASB Component 和 ComponentVersion，保存本次发布的关联清单"""
    # 注意：此组件会创建 SG 实体。按实体 ID 查询，重试时复用本次已创建的记录。
    try:
        Component.use_script(API_SCRIPTS.version_up_tool)
        tc = TaskContext(process_data['task_id'])
        if tc.entity.sg_asset_type != 'ASB':
            raise RuntimeError('仅支持 ASB 资产')
        components = process_data['asb_components']
        if not components:
            raise RuntimeError('没有待登记的 ASB Component')
        project = {'type': 'Project', 'id': tc.project.id}
        entity = {'type': 'Asset', 'id': tc.entity.id}
        task = {'type': 'Task', 'id': tc.task.id}
        scope = (tc.task.id, process_data['version_name'])
        if process_data.get('asb_component_scope') != scope:
            process_data['asb_component_scope'] = scope
            process_data['asb_component_records'] = {}
        records = process_data['asb_component_records']
        for path in components:
            if path in records:
                continue
            code = path.strip('/').replace('/', '.')
            matches = Component.filter(filters=[
                ['code', 'is', code], ['project', 'is', project],
                ['sg_entity', 'is', entity], ['sg_task', 'is', task]])
            if len(matches) > 1:
                raise RuntimeError('存在重复 Component: ' + code)
            if matches:
                component = matches[0]
            else:
                component = Component.create(code=code, project=project, sg_entity=entity,
                                             sg_task=task, sg_step={'type': 'Step', 'id': tc.step.id})
            comp_ref = {'type': 'CustomEntity09', 'id': component.id}
            versions = ComponentVersion.filter(filters=[['sg_component', 'is', comp_ref]], fields=['code'])
            numbers = []
            for version in versions:
                match = re.search(r'\.v(\d+)$', version.code, re.IGNORECASE)
                if match:
                    numbers.append(int(match.group(1)))
            number = max(numbers, default=0) + 1
            version = ComponentVersion.create(
                code=code + '.v{0:03d}'.format(number), sg_component=comp_ref,
                sg_entity=entity, project=project, sg_task=task)
            records[path] = {'component': comp_ref,
                             'component_version': {'type': 'CustomEntity08', 'id': version.id}}
        process_data['asb_component_links'] = [records[p]['component'] for p in components]
        process_data['asb_component_version_links'] = [records[p]['component_version'] for p in components]
        logger.info('已登记 {0} 个 ASB ComponentVersion'.format(len(components)))
    except Exception:
        return traceback.format_exc()
