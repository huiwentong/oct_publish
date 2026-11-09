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
from qtpy import QtWidgets


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查 picker 文件"""
    try:
        task_id = process_data.get("task_id")
        tc = TaskContext(task_id) or TaskContext.from_env()
        sg_asset_type = tc.entity.sg_asset_type
        if sg_asset_type != "CH":
            logger.info("当前资产不是角色(CH)，已跳过")
            return ""

        task_name = tc.task_name.lower()
        if task_name != 'rigging':
            logger.info("当前任务不是rigging，已跳过")
            return ""

        asset_name = tc.entity_name
        picker_file_name = "{}.mgpkr".format(asset_name)
        file_name_list = ['Body_PkrImage.bmp', 'cloth.jpg', 'face.jpg', 'hair.jpg', 'default.mgpkr', picker_file_name]

        # 去掉空项
        submit_data['submit_picker_files'] = [f for f in submit_data['submit_picker_files'] if f]
        submit_picker_files = submit_data["submit_picker_files"]

        mgpkr_l = [f for f in submit_picker_files if f.endswith('.mgpkr')]
        if len(mgpkr_l) != 1:
            return u".mgpkr 文件数量不对，应该是 1 个"

        mgpkr = mgpkr_l[0]
        default_template = 'W:/projects/lib/Ani_lib/MG_picker/MK2/default_template'
        if (os.path.basename(mgpkr) == 'default.mgpkr' and
                not mgpkr.replace('\\', '/').lower().startswith(default_template.lower())):
            return u"请将 mgpkr 文件改名，如果是默认的 mgpkr 文件，则必须来自 {}".format(default_template)

        if submit_picker_files and len(submit_picker_files) == 5:
            for f in submit_picker_files:
                if not os.path.exists(f):
                    return u"文件不存在 {}".format(f)

            for file_name in [os.path.basename(f) for f in submit_picker_files]:
                if file_name not in file_name_list:
                    return u"上传的Picker文件不对 - {0}，应该是 {1} 或 {2}， 一共5个".format(
                        file_name, ', '.join(file_name_list[0: -1]), picker_file_name)
            return u""
        else:
            return u"上传的Picker文件不对，应该是 {0} 或 {1}， 一共5个".format(
                ', '.join(file_name_list[0: -1]), picker_file_name)

    except Exception:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    task_id = process_data.get("task_id")
    tc = TaskContext(task_id) or TaskContext.from_env()
    asset_name = tc.entity_name
    upper_project_name = tc.project_name.upper()

    picker_root = "W:/projects/lib/Ani_lib/MG_picker"
    default_template = 'W:/projects/lib/Ani_lib/MG_picker/MK2/default_template'
    proj_picker_dir = picker_root + '/' + upper_project_name
    asset_picker_dir = proj_picker_dir + '/' + asset_name

    if os.path.isdir(asset_picker_dir):
        default_dir = asset_picker_dir
    elif os.path.isdir(default_template):
        default_dir = default_template
    elif os.path.isdir(proj_picker_dir):
        default_dir = proj_picker_dir
    else:
        default_dir = picker_root

    file_paths, _ = QtWidgets.QFileDialog.getOpenFileNames(
        parent_widget,
        "选择Picker相关文件",
        default_dir,
        "所有文件 (*);;"
        "Picker 文件 (*.mgpkr);;"
        "Body_PkrImage (*.bmp);;"
        "cloth (*.jpg);;"
        "face (*.jpg);;"
        "hair (*.jpg);"
    )
    picker_file_name = "{}.mgpkr".format(asset_name)
    if len(file_paths or []) != 5:
        return u"请一次性选中 {}或default.mgpkr, Body_PkrImage.bmp, cloth.jpg, face.jpg, hair.jpg，一共5个文件".format(
            picker_file_name)

    if file_paths:
        submit_data['submit_picker_files'] = [f.replace('\\', '/') for f in file_paths]
    print(submit_data['submit_picker_files'])

    # if main(submit_data, process_data, parent_widget, logger):

# def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
#     def _move_rename(source, target):
#         try:
#             if not os.path.exists(source):
#                 logger.warning(f"错误：源文件不存在 - {source}")
#                 return False
#
#             if os.path.exists(target):
#                 logger.info(f"目标文件已存在，跳过 - {target}")
#                 return True
#
#             else:
#                 destination_dir = os.path.dirname(target)
#                 if not os.path.exists(destination_dir):
#                     path_acs.make_dirs(destination_dir)
#                 shutil.copy2(source, target)
#                 logger.info(f"复制完成: {0} -> {1}".format(source, target))
#                 return True
#
#         except Exception as e:
#             logger.error('复制失败: {}'.format(str(e)))
#             return False
#
#     try:
#         file_name_list = ['Body_PkrImage.bmp', 'cloth.jpg', 'face.jpg', 'hair.jpg', 'default.mgpkr']
#         default_picker_dir = "W:/projects/lib/Ani_lib/MG_picker/MK2/default_template"
#         default_picker_file_list = [default_picker_dir + '/{}'.format(f) for f in file_name_list]
#         picker_file_list = process_data['picker_file_list']
#         msg = ''
#         for source, target in zip(default_picker_file_list, picker_file_list):
#             done = _move_rename(source, target)
#             if not done:
#                 msg += '复制失败: {} -> {},  '.format(source, target)
#
#         if msg:
#             return msg
#
#     except Exception:
#         return traceback.format_exc()
