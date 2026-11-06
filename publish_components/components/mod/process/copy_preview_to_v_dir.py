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

        origin_dir = os.path.dirname(v_dir_preview) + '/origin'
        if not os.path.exists(origin_dir):
            os.makedirs(origin_dir)

        task = SGEntity('Task', process_data['task_id'])
        entity = task.entity
        l_img_files = l_preview_files[:]
        if entity.type == "Shot" and \
            task.step.code in ['Ef', 'Lgt', 'Cm'] and \
                entity.sg_cut_duration:
            duration = entity.sg_cut_duration
        else:
            duration = len(l_img_files)

        entity_name = task.entity.code
        ordered_files = ['', '', '']
        name_map = {
            f"{entity_name}_Whole.mov": 0,
            f"{entity_name}_Uper.mov": 1,
            f"{entity_name}_Closeup.mov": 2,
        }
        if len(l_img_files) == 3 and all(f.endswith(".mov") for f in l_img_files):
            for f in l_img_files:
                idx = name_map.get(str(os.path.basename(f)))
                if idx is not None:
                    ordered_files[idx] = f

            if not all(ordered_files):
                return u"输出预览文件失败，文件不规范，排序失败"

            for f in ordered_files:
                shutil.copy2(f, origin_dir)

        is_deadline_job = process_data.get("is_deadline_job")

        if ordered_files:
            duration = 3
            if is_deadline_job:
                create_shot_mov.create(ordered_files, v_dir_preview, duration, resolution=(720, 720), use='ffmpeg')
            else:
                create_shot_mov.create(ordered_files, v_dir_preview, duration, resolution=(720, 720))

        elif l_img_files:
            if is_deadline_job:
                create_shot_mov.create(l_img_files, v_dir_preview, duration, use='ffmpeg')
            else:
                create_shot_mov.create(l_img_files, v_dir_preview, duration)

        logger.info('v_dir_preview: ' + v_dir_preview)
        if not os.path.isfile(v_dir_preview):
            return u"输出预览文件失败: " + v_dir_preview
    except:
        return traceback.format_exc()


