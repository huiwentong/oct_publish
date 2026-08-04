import traceback
import inspect
import time
import os
import shutil
import subprocess
from publish_core.database.entity import SGEntity


def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
向版本文件夹 拷贝/创建 版本预览mov文件
    """

    try:
        task = SGEntity('Task', process_data['task_id'])
        v_dir_preview = process_data['v_dir'] + '/preview'
        l_preview_files = process_data['preview_paths']
        if len(l_preview_files) and l_preview_files[0].lower().endswith('.mov'):
            src = l_preview_files[0]
            dst = v_dir_preview
            shutil.copyfile(src, dst)
        else:
            from publish_components.utils import create_shot_mov
            l_img_files = l_preview_files

            if task.entity['type'] == 'Shot' and task.step['name'] in ['Ef', 'Lgt', 'Cm'] and \
                    task.entity['sg_cut_duration']:
                duration = task.entity['sg_cut_duration']
            else:
                duration = len(l_img_files)

            if l_img_files:
                create_shot_mov.create(l_img_files, v_dir_preview, duration)

        logger.info('self.dialog.v_dir_preview: ' + v_dir_preview)
        if not os.path.isfile(v_dir_preview):
            return u"输出预览文件失败: " + v_dir_preview

    except:
        return traceback.format_exc()