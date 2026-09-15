# coding=utf-8
import importlib
import traceback

from oct.pipeline.shotgun.config import API_SCRIPTS
from oct.pipeline.shotgun.models import Version
from publish_components.components.maya_shot.process.update_sg_version import main as update_shot_version


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None) -> str | None:
    """复用镜头 SG 更新，并登记旧 blk/ani 的 asset.cocoVersion 客户版本号。"""
    try:
        # Dailies 可在 Maya 外运行：只在完整发布时动态加载 Maya 模块。
        coco_version = None
        if process_data.get('publish_type') in ('Submit', 'Publish'):
            maya_commands = importlib.import_module('maya.cmds')
            maya_thread_utils = importlib.import_module('maya.utils')
            coco_version = maya_thread_utils.executeInMainThreadWithResult(
                lambda: maya_commands.getAttr('asset.cocoVersion')
                if maya_commands.objExists('asset.cocoVersion') else None)
        result = update_shot_version(submit_data, process_data, parent_widget, logger)
        if result:
            return result
        if coco_version is not None:
            # 注意：修改 SG Version.client_code，保留旧流程的客户版本登记。
            Version.use_script(API_SCRIPTS.version_up_tool)
            version = Version.get(id=process_data['sg_version']['id'])
            version.client_code = coco_version
            version.save()
    except Exception:
        return traceback.format_exc()
