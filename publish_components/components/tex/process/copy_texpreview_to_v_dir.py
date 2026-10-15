# -*- coding: utf-8 -*-

import os
import shutil
import traceback
from publish_components.utils import create_shot_mov

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """向版本文件夹拷贝 / 创建版本预览 mov 文件"""
    try:
        preview_files = process_data["preview_paths"]
        preview_mov = process_data["v_dir_preview"]
        version_dir = process_data["version_dir"]

        mov_files = [
            path for path in preview_files
            if path.lower().endswith(".mov")
        ]
        img_files = [
            path for path in preview_files
            if not path.lower().endswith(".mov")
        ]
        duration = len(img_files)
        if img_files:
            is_deadline_job = process_data.get("is_deadline_job")
            if is_deadline_job:
                create_shot_mov.create(img_files, preview_mov, duration, use='ffmpeg')
            else:
                create_shot_mov.create(img_files, preview_mov, duration)
            extra_movs = mov_files
        else:
            shutil.copyfile(mov_files[0], preview_mov)
            extra_movs = mov_files[1:]

        preview_dir = os.path.join(version_dir, "preview")

        for mov in extra_movs:
            shutil.copy(mov, os.path.join(preview_dir, os.path.basename(mov)))
        logger.info("Preview mov: {}".format(preview_mov))

        if not os.path.isfile(preview_mov):
            return "输出预览文件失败: {}".format(preview_mov)

    except Exception:
        return traceback.format_exc()
