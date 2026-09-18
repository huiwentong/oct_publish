# -*- coding: utf-8 -*-

import os, glob, shutil, traceback


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """查找 rig 环节的 pre_cam.abc，并拷贝到当前版本 tmp_cam 目录。"""
    try:
        version_dir = process_data.get("version_dir")
        if not version_dir:
            return u"没有获取到 version_dir"

        asset_root = os.path.dirname(os.path.dirname(version_dir.rstrip("/\\")))
        pattern = os.path.join(asset_root, "rig", "*.rig.rigging", "tmp_cam", "pre_cam.abc")
        pre_cams = glob.glob(pattern)
        if not pre_cams:
            return ""

        tmp_cam_dir = os.path.join(version_dir, "tmp_cam")
        if not os.path.isdir(tmp_cam_dir):
            os.makedirs(tmp_cam_dir)

        target = os.path.join(tmp_cam_dir, "pre_cam.abc")
        shutil.copy(pre_cams[0], target)

        if logger:
            logger.info(u"Pre Cam 缓存拷贝完成：{}".format(target.replace("\\", "/")))
        return ""
    except Exception:
        return traceback.format_exc()