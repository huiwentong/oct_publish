# -*- coding: utf-8 -*-
import traceback
from oct.pipeline.shotgun.models import Component, Version
from oct.pipeline.shotgun.config import API_SCRIPTS

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """将本次 ComponentVersion 关联到刚创建的 SG Version"""
    # 注意：此组件写入 SG 关联字段，保留 Component 已有的历史 Version 关联。
    try:
        Version.use_script(API_SCRIPTS.version_up_tool)
        version_ref = process_data['sg_version']
        version = Version.get(id=version_ref['id'])
        if version.sg_task.id != process_data['task_id'] or version.code != process_data['version_name']:
            raise RuntimeError('待关联 SG Version 与本次任务/版本不一致')
        links = process_data['asb_component_version_links']
        version.sg_component_versions = links
        version.save()
        for comp_ref in process_data['asb_component_links']:
            component = Component.get(id=comp_ref['id'], fields=['sg_versions'])
            previous = list(component.sg_versions or [])
            ids = [item['id'] if isinstance(item, dict) else item.id for item in previous]
            if version.id not in ids:
                previous.append({'type': 'Version', 'id': version.id})
                component.sg_versions = previous
                component.save()
        logger.info('已关联 SG Version {0} 与 {1} 个 ComponentVersion'.format(version.id, len(links)))
    except Exception:
        return traceback.format_exc()
