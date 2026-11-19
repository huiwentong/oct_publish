# -*- coding: utf-8 -*-
import shutil
import traceback


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    把各镜头的拍屏拷到镜头版本文件夹的 preview 下，按镜头版本号命名
    """
    # Deadline 建镜头 SG Version 时上传的就是这个 mov。
    # 不再拷到镜头工作目录：camera_sequencer_creator_2024 拍屏时已经直接输出到那里，镜头表格抓的就是它。
    try:
        for shot, info in process_data['linked_task_info'].items():
            shutil.copyfile(info['preview'], info['v_preview'])
            logger.info(u'{0}: {1}'.format(shot, info['v_preview']))
    except:
        return traceback.format_exc()
