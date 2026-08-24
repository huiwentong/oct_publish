# -*- coding: utf-8 -*-
import traceback, os
from PIL import Image
import pymel.core as pm
from oct.pipeline.task_context import TaskContext
def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查角色模型贴图尺寸，S, A, B 级资产贴图尺寸限制为 1024, 其他资产贴图尺寸限制为 512"""
    try:
        task_id = process_data['task_id']
        tc = TaskContext(task_id) or TaskContext.from_env()

        def _get_image_size(image_path):
            with Image.open(image_path) as img:
                return img.width, img.height

        if tc.entity.sg_asset_type == "CH":
            asset = tc.entity
            error_list = []
            if asset and asset.sg_level and asset.sg_level in ('S', 'A', 'B'):
                target_resolution = 1024
            else:
                target_resolution = 512


            for node in pm.ls(type=['file', 'aiImage']):
                try:
                    tex_path = node.fileTextureName.get()
                except:
                    tex_path = node.filename.get()

                wide, high = _get_image_size(tex_path)
                if wide > target_resolution or high > target_resolution:
                    error_list.append(f'{node.name()} {wide}x{high}')

            if error_list:
                return "\n".join(
                    error_list) + f"\n以上贴图尺寸超过限制, 当前资产级别为{asset.sg_level},尺寸建议为{target_resolution}"

    except Exception:
        return traceback.format_exc()
