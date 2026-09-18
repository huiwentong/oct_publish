# -*- coding: utf-8 -*-

import os, glob, shutil, traceback
import maya.cmds as cmds
import maya.mel as mel
import maya.utils as utils
import xgenm as xg
from oct.pipeline import path_acs


def _save_scene(file_path):
    """保存当前 Maya 场景。"""
    file_path = str(file_path).replace("\\", "/").replace('"', '\\"')
    mel.eval('file -rename "{}";'.format(file_path))
    mel.eval('file -save -force -type "mayaAscii";')


def _process(process_data, logger=None):
    """拷贝并重定向 Fur 发布依赖。"""
    work_space_root = process_data.get("work_space_root")
    version_dir = process_data.get("version_dir")
    palette = process_data.get("xgen_palette_name")
    v_dir_ma_file = process_data.get("v_dir_ma_file")

    if not work_space_root:
        return u"没有获取到 work_space_root"
    if not version_dir:
        return u"没有获取到 version_dir"
    if not palette:
        return u"没有获取到 xgen_palette_name"
    if not v_dir_ma_file:
        return u"没有获取到 v_dir_ma_file"

    src = "{}/xgen/collections/{}".format(work_space_root.rstrip("/"), palette)
    target = "{}/xgen/collections/{}".format(version_dir.rstrip("/"), palette)
    if os.path.exists(target):
        shutil.rmtree(target)
    shutil.copytree(src, target)

    origin_paths = {"files": {}}
    xg_data_path = xg.getAttr("xgDataPath", str(palette))
    origin_paths["xgDataPath"] = xg_data_path
    folder_name = xg_data_path.replace("\\", "/").split("xgen/")[-1]
    xg.setAttr("xgDataPath", "{}/xgen/{}".format(version_dir.rstrip("/"), folder_name), str(palette))
    process_data["origin_paths"] = origin_paths

    file_dic = {}
    for node in cmds.ls(type=["file", "aiImage"]) or []:
        if cmds.nodeType(node) == "file":
            image_path = cmds.getAttr(node + ".computedFileTextureNamePattern")
        else:
            image_path = cmds.getAttr(node + ".filename")
        if not image_path:
            continue
        image_path = image_path.replace("\\", "/")
        if image_path.lower().startswith("i:/"):
            continue
        file_dic[node] = image_path

    source_images = []
    for image_path in file_dic.values():
        paths = glob.glob(image_path.replace("<UDIM>", "*")) if "<UDIM>" in image_path else [image_path]
        for path in paths:
            path = path.replace("\\", "/")
            if path not in source_images:
                source_images.append(path)

    target_dir = "{}/sourceimages_hair".format(version_dir.rstrip("/"))
    if not os.path.exists(target_dir):
        path_acs.make_dirs(target_dir)

    if logger:
        logger.info(u"开始拷贝毛发贴图")

    for image in source_images:
        if not os.path.isfile(image):
            continue
        target_image = "{}/{}".format(target_dir, os.path.basename(image))
        if not os.path.exists(target_image):
            shutil.copy2(image, target_image)

    for node, image_path in file_dic.items():
        target_path = "{}/{}".format(target_dir, os.path.basename(image_path))
        if cmds.nodeType(node) == "file":
            cmds.setAttr(node + ".fileTextureName", target_path, type="string")
        else:
            cmds.setAttr(node + ".filename", target_path, type="string")

    _save_scene(v_dir_ma_file)
    return ""


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """拷贝资产依赖的 XGen 数据和贴图到版本目录，并重新设置引用路径。"""
    try:
        result = utils.executeInMainThreadWithResult(_process, process_data, logger)
        return result or ""
    except Exception:
        return traceback.format_exc()