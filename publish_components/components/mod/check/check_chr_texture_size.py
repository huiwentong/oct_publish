# -*- coding: utf-8 -*-
import traceback, os
from PIL import Image
import pymel.core as pm
import maya.utils as utils
from oct.pipeline.task_context import TaskContext

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查角色模型贴图尺寸，S, A, B 级资产贴图尺寸限制为 1024, 其他资产贴图尺寸限制为 512"""
    try:
        def _get_image_size(image_path):
            with Image.open(image_path) as img:
                return img.width, img.height

        def _check():
            error_list = []
            for node in pm.ls(type=['file', 'aiImage']):
                if pm.referenceQuery(node, isNodeReferenced=True):
                    continue
                try:
                    tex_path = node.fileTextureName.get()
                except:
                    tex_path = node.filename.get()

                wide, high = _get_image_size(tex_path)
                if wide > target_resolution or high > target_resolution:
                    error_list.append(f'{node.name()} {wide}x{high}')

            return error_list


        task_id = process_data['task_id']
        publish_tag_id = process_data['publish_tag_id']
        tc = TaskContext(task_id) or TaskContext.from_env()

        #只有资产类型时 CH 并且 tag 不为 “低模”的时候才检查
        if tc.entity.sg_asset_type == "CH" and publish_tag_id != 1129:
            asset = tc.entity
            if asset and asset.sg_level and asset.sg_level in ('S', 'A', 'B'):
                target_resolution = 1024
            else:
                target_resolution = 512

            e_list = utils.executeInMainThreadWithResult(_check)
            if e_list:
                return "\n".join(e_list) + f"\n以上贴图尺寸超过限制, 当前资产级别为{asset.sg_level},尺寸建议为{target_resolution}"

    except Exception:
        return traceback.format_exc()
