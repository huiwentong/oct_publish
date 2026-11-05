# -*- coding: utf-8 -*-
import traceback
import os
import shutil
from copy import deepcopy
from pathlib import Path
from oct.pipeline import path_acs

import pymel.core as pm
import maya.utils as utils
from oct.pipeline.task_context import TaskContext


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查 picker 文件是否存在"""
    try:
        file_name_list = ['Body_PkrImage.bmp', 'cloth.jpg', 'face.jpg', 'hair.jpg']
        picker_root = "W:/projects/lib/Ani_lib/MG_picker"

        task_id = process_data.get("task_id")
        tc = TaskContext(task_id) or TaskContext.from_env()
        sg_asset_type = tc.entity.sg_asset_type
        if sg_asset_type != "CH":
            logger.info("当前资产不是角色(CH)，已跳过")
            return ""
        project_name = tc.project_name.lower()
        asset_name = tc.entity_name
        picker_file_name = "{}.mgpkr".format(asset_name)
        file_name_list.append(picker_file_name)
        picker_file_list = [Path(picker_root) / project_name.upper() / asset_name / f for f in file_name_list]
        process_data['picker_file_list'] = [str(p).replace('\\', '/') for p in picker_file_list]

        if not all([p.exists() for p in picker_file_list]):
            return u"Picker文件有缺失，请检查:{}".format(', '.join(process_data['picker_file_list']))
        else:
            return ""
    except Exception:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    def _move_rename(source, target):
        try:
            if not os.path.exists(source):
                logger.warning(f"错误：源文件不存在 - {source}")
                return False
            else:
                destination_dir = os.path.dirname(target)
                if not os.path.exists(destination_dir):
                    path_acs.make_dirs(destination_dir)
                shutil.copy2(source, target)
                logger.info(f"复制完成: {0} -> {1}".format(source, target))
                return True

        except Exception as e:
            logger.error('复制失败: {}'.format(str(e)))
            return False

    try:
        file_name_list = ['Body_PkrImage.bmp', 'cloth.jpg', 'face.jpg', 'hair.jpg', 'default.mgpkr']
        default_picker_dir = "W:/projects/lib/Ani_lib/MG_picker/MK2/default_template"
        default_picker_file_list = [default_picker_dir + '/{}'.format(f) for f in file_name_list]
        picker_file_list = process_data['picker_file_list']
        msg = ''
        for source, target in zip(default_picker_file_list, picker_file_list):
            done = _move_rename(source, target)
            if not done:
                msg += '复制失败: {} -> {},  '.format(source, target)

        if msg:
            return msg

    except Exception:
        return traceback.format_exc()
