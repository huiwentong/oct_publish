# -*- coding: utf-8 -*-
import json
import traceback

from publish_core.database.entity import SGEntity


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    把各镜头 build shot file 任务要用的信息写成场次版本目录下的 seq_lay_shots.json
    """
    # 格式 {镜头: info}，Deadline 的 lay_seq_output_shot_2024 按镜头名读取。
    # 必须在 gen/lock_v_dir 之前：之后场次版本目录就锁了。
    # 文件随场次版本归档，事后可查每个镜头提交了什么；在 Deadline 上重新排队也会读同一份。
    # 提交人用 process_data['user']，农场机器上的 username 是服务账号。
    try:
        tag_name = SGEntity('Tag', process_data['publish_tag_id']).name
        shots_info = {}
        for shot, info in process_data['linked_task_info'].items():
            shots_info[shot] = {
                'version_dir': info['version_dir'],
                'work_dir': info['work_dir'],
                'start_f': info['start_f'],
                'end_f': info['end_f'],
                'v_preview': info['v_preview'],
                'user': process_data['user'],
                'description': process_data.get('comment') or '',
                'tag': tag_name,
            }
        json_file = process_data['version_dir'] + '/seq_lay_shots.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(shots_info, f, ensure_ascii=False, indent=2)
        process_data['shot_job_info_file'] = json_file
        logger.info(u'镜头任务信息: {0}'.format(json_file))
    except:
        return traceback.format_exc()
