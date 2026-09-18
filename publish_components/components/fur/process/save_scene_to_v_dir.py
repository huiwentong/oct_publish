# -*- coding: utf-8 -*-

import traceback

import maya.mel as mel
import maya.utils as utils


def _save_scene(v_dir_ma_file):
    """将当前 Maya 场景另存到发布版本目录。"""
    file_path = str(v_dir_ma_file).replace("\\", "/")
    file_path = file_path.replace('"', '\\"')

    mel.eval('file -rename "{}";'.format(file_path))

    mel.eval('file -save -force -type "mayaAscii";')


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """另存场景 ma 到版本文件夹。"""
    try:
        v_dir_ma_file = process_data.get("v_dir_ma_file")

        if not v_dir_ma_file:
            return u"没有获取到 v_dir_ma_file"

        utils.executeInMainThreadWithResult(_save_scene, v_dir_ma_file)

        if logger:
            logger.info(u"场景保存完成：{}".format(v_dir_ma_file))

        return ""

    except Exception:
        return traceback.format_exc()