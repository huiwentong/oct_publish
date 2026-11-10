# -*- coding: utf-8 -*-
import traceback

import maya.cmds as cmds
import maya.utils as utils

from publish_components.utils import images


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    检查提交的预览文件帧数与文件播放范围一致
    """
    # 预览必须完整对应当前文件的播放范围，不一致说明预览没拍全，需要重拍；不允许跳过。
    # 文件范围和 SG 是否一致由 check_file_frame_range 负责。
    try:
        def sync_anim_range():
            # 顺手把动画范围同步成播放范围
            start_f = cmds.playbackOptions(q=True, min=True)
            end_f = cmds.playbackOptions(q=True, max=True)
            cmds.playbackOptions(e=True, ast=start_f, aet=end_f)
            return int(end_f) - int(start_f) + 1

        duration = utils.executeInMainThreadWithResult(sync_anim_range)

        # mov 逐个比帧数；图片由 copy_preview_to_v_dir 按“一张一帧”拼成 mov，所以按总张数比，
        # 只截一张图当预览是过不了的
        image_files = []
        for preview in process_data.get('preview_paths', []):
            preview = str(preview)
            if preview.lower().endswith('.mov'):
                res_x, res_y, frames = images.get_info_by_ffprobe(preview)
                if int(frames) != duration:
                    return u"{0} 的帧数为 {1}，与文件播放范围的帧数 {2} 不一致。".format(
                        preview, frames, duration)
            else:
                image_files.append(preview)

        if image_files and len(image_files) != duration:
            return u"提交了 {0} 张图片作为预览，与文件播放范围的帧数 {1} 不一致，请提交完整帧数的序列帧或 mov。".format(
                len(image_files), duration)
    except:
        return traceback.format_exc()
