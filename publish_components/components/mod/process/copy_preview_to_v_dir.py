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

        ordered_files = []
        formated_mov_dic = process_data.get('formated_mov_dic', {})
        group_order = ['whole', 'uper', 'closeup']
        logger.info(sorted(list(formated_mov_dic.keys())))
        for middle in sorted(list(formated_mov_dic.keys())):
            group = formated_mov_dic[middle]
            temp = ['', '', '']
            for itm, f in group.items():
                idx = group_order.index(itm)
                temp[idx] = f
            if all(temp):
                ordered_files.extend(temp)

        logger.info("ordered_files: {}".format(str(ordered_files)))
        for f in ordered_files:
            shutil.copy2(f, origin_dir)

        is_deadline_job = process_data.get("is_deadline_job")
        if ordered_files:
            process_data['ordered_files'] = ordered_files
            duration = len(ordered_files)
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


