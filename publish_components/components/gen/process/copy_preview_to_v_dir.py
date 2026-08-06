# -*- coding: utf-8 -*-
import os
import shutil
import traceback
from publish_components.utils import create_shot_mov
from publish_core.database.entity import SGEntity
from oct.pipeline.path_acs import old_get_path, unlock_path, make_dirs

def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
    向版本文件夹 拷贝/创建 版本预览mov文件
    """

    try:
        v_dir_preview = process_data.get("v_dir_preview")
        l_preview_files = process_data.get("preview_paths", [])
        task = SGEntity('Task', process_data['task_id'])
        entity = task.entity
        if len(l_preview_files) and l_preview_files[0].lower().endswith('.mov'):
            src = l_preview_files[0]
            dst = v_dir_preview
            shutil.copyfile(src, dst)
        else:
            l_img_files = l_preview_files[:]
            if entity.type == "Shot" and \
                task.step.code in ['Ef', 'Lgt', 'Cm'] and \
                    entity.sg_cut_duration:
                duration = entity.sg_cut_duration
            else:
                duration = len(l_img_files)

            if l_img_files:
                is_deadline_job = process_data.get("is_deadline_job")
                if is_deadline_job:
                    create_shot_mov.create(l_img_files, v_dir_preview, duration, use='ffmpeg')
                else:
                    create_shot_mov.create(l_img_files, v_dir_preview, duration)

            logger.info('v_dir_preview: ' + v_dir_preview)
            if not os.path.isfile(v_dir_preview):
                return u"输出预览文件失败: " + v_dir_preview
    except:
        return traceback.format_exc()


