# -*- coding: utf-8 -*-
import os,glob,shutil,traceback

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """查找 rig 环节的 pre_cam.abc，并拷贝到当前版本 tmp_cam 目录。"""
    try:
        version_dir=process_data.get("version_dir")
        modCamPattern = os.path.dirname(os.path.dirname(version_dir)) + "/rig/*.rig.rigging/tmp_cam/pre_cam.abc"
        modCam = glob.glob(modCamPattern)
        if modCam:
            pre_cam_path = version_dir + '/tmp_cam/pre_cam.abc'
            if not os.path.isdir(version_dir + '/tmp_cam'):
                os.makedirs(version_dir + '/tmp_cam')
            shutil.copy(modCam[0], pre_cam_path)

    except Exception:
        return traceback.format_exc()