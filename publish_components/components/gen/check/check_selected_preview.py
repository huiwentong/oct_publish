# -*- coding: utf-8 -*-
import json
import os
import subprocess
import traceback
from collections import defaultdict
from typing import Any

from publish_core.database.entity import SGEntity


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    检查提交预览文件的路径和命名
    """
    # 检查提交的预览文件是否存在，扩展名是否有效

    SUFFIX_MAP = {
        '_Whole.mov': 'whole',
        '_Uper.mov': 'uper',
        '_Closeup.mov': 'closeup',
    }

    def _default_dict():
        return {'whole': '', 'uper': '', 'closeup': ''}

    formated_mov_dic = defaultdict(_default_dict)

    try:
        input_preview_files = process_data.get("preview_paths", [])

        l_preview_files = []
        l_pur_files = []
        if len(input_preview_files) == 0:
            return u"还没有选择文件。"

        for file_path_str in input_preview_files:
            file_path = str(file_path_str)

            if not os.path.isfile(file_path):
                return u"找不到这个文件:\n  " + file_path

            if os.path.basename(file_path).lower().endswith('.pur'):
                l_pur_files.append(file_path)
            else:
                l_preview_files.append(file_path)

        if len(l_preview_files) == 0:
            return u"没有给出图片或者 mov 文件，无法生成版本预览"

        task = SGEntity('Task', process_data['task_id'])
        entity_name = task.entity.code
        if task.step.code in ['mod', 'Texture']:
            mov_files = [f for f in l_preview_files if f.endswith('.mov')]

            # 检查视频数量
            if len(mov_files) % 3 != 0 or not all(
                    [f.split('_')[-1] in ['Whole.mov', 'Uper.mov', 'Closeup.mov'] for f in mov_files]):
                return u"预览视频每一组都需要包含 _Whole.mov，_Uper.mov，_Closeup.mov"

            # 检查文件格式
            if mov_files and len(mov_files) != len(l_preview_files):
                return u"预览文件如果是 mov 视频，则不可以上传其他格式文件"

            for f in mov_files:

                # 检查视频名称
                if not os.path.basename(f).startswith(entity_name + '_'):
                    return u"文件名需要以资产名 {}_ 开头".format(entity_name)

                # 构建字典，以中段作为键
                fn = os.path.basename(f)
                middle = fn[len(entity_name):-len(fn.split('_')[-1])].strip('_')
                for suffix, key in SUFFIX_MAP.items():
                    if fn.endswith(suffix):
                        formated_mov_dic[middle][key] = f
                        break

            for middle, group in formated_mov_dic.items():
                for k, f in group.items():
                    if not f:
                        return u"预览视频每一组都需要包含 _Whole.mov，_Uper.mov，_Closeup.mov"

            # 检查视频分辨率
            for f in mov_files:
                cmd = (
                    f'rez-env ffmpeg -- ffprobe -v error -select_streams v:0 '
                    f'-show_entries stream=width,height,r_frame_rate,duration '
                    f'-of json "{f}"'
                )

                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
                data = json.loads(result.stdout)
                stream = data["streams"][0]
                width = stream["width"]
                height = stream["height"]
                if not (width == 2048 and height == 2048):
                    return u"视频分辨率错误，应该是 2048 * 2048 : {}".format(f)

                num, den = stream["r_frame_rate"].split("/")
                fps = float(num) / float(den) if float(den) else 0.0
                duration = float(stream.get("duration") or 0)
                total_frames = int(round(duration * fps))
                if total_frames != 50:
                    return u"视频帧数错误，应该是50帧 : {}".format(f)

        process_data.update({"preview_paths": l_preview_files,
                             "pur_files": l_pur_files,
                             "formated_mov_dic": formated_mov_dic})
        logger.info("formated_mov_dic: {}".format(formated_mov_dic))
        logger.info(sorted(list(formated_mov_dic.keys())))
        logger.info("l_preview_files: {}".format(l_preview_files))
        logger.info("l_pur_files: {}".format(l_pur_files))
    except:
        return traceback.format_exc()
