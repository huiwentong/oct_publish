# -*- coding: utf-8 -*-
import traceback

import maya.cmds as cmds
import maya.utils as utils

from oct.pipeline.task_context import TaskContext
from publish_components.utils import images


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    检查提交的预览文件帧数与 SG 上镜头时长一致
    """
    # 预览文件的帧数必须和 SG 上镜头的 cut 时长一致，不一致需要确认时长并重拍；不允许跳过。
    try:
        def sync_anim_range():
            # 顺手把动画范围同步成播放范围
            start_f = cmds.playbackOptions(q=True, min=True)
            end_f = cmds.playbackOptions(q=True, max=True)
            cmds.playbackOptions(e=True, ast=start_f, aet=end_f)

        utils.executeInMainThreadWithResult(sync_anim_range)

        tc = TaskContext(process_data['task_id'])
        if tc.entity_type != 'Shot':
            return u"当前实体不是镜头：{0}".format(tc.entity_type)
        shot = tc.entity
        sg_cut_in = shot.sg_cut_in
        sg_cut_out = shot.sg_cut_out
        if sg_cut_in is None or sg_cut_out is None:
            return u"SG 上镜头 {0} 没有填写 cut in / cut out，请找制片确认".format(tc.entity_name)
        sg_cut_duration = int(sg_cut_out) - int(sg_cut_in) + 1

        # mov 逐个比帧数；图片由 copy_preview_to_v_dir 按“一张一帧”拼成 mov，所以按总张数比，
        # 只截一张图当预览是过不了的
        image_files = []
        for preview in process_data.get('preview_paths', []):
            preview = str(preview)
            if preview.lower().endswith('.mov'):
                res_x, res_y, frames = images.get_info_by_ffprobe(preview)
                if int(frames) != sg_cut_duration:
                    return u"{0} 的帧数为 {1}，与 shotgun 上记录的帧数 {2} 不一致。".format(
                        preview, frames, sg_cut_duration)
            else:
                image_files.append(preview)

        if image_files and len(image_files) != sg_cut_duration:
            return u"提交了 {0} 张图片作为预览，与 shotgun 上记录的帧数 {1} 不一致，请提交完整帧数的序列帧或 mov。".format(
                len(image_files), sg_cut_duration)
    except:
        return traceback.format_exc()
