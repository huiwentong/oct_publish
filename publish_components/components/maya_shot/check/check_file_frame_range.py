# -*- coding: utf-8 -*-
import traceback

import maya.cmds as cmds
import maya.utils as utils

from oct.pipeline.task_context import TaskContext


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    检查文件帧范围与 SG 上镜头 cut in / cut out 一致
    """
    # 文件的播放范围必须和 SG 上镜头的 cut in / cut out 完全一致，不一致需要找动画制片确认镜头时长；不允许跳过。
    try:
        tc = TaskContext(process_data['task_id'])
        # TaskContext 进程内缓存，不刷新的话 SG 改了 cut in / out 重跑检查也拿不到
        tc.refresh()
        if tc.entity_type != 'Shot':
            return u"当前实体不是镜头：{0}".format(tc.entity_type)
        shot = tc.entity
        sg_cut_in = shot.sg_cut_in
        sg_cut_out = shot.sg_cut_out
        if sg_cut_in is None or sg_cut_out is None:
            return u"SG 上镜头 {0} 没有填写 cut in / cut out，请找制片确认".format(tc.entity_name)

        def frame_range():
            return (int(cmds.playbackOptions(q=True, min=True)),
                    int(cmds.playbackOptions(q=True, max=True)))

        start, end = utils.executeInMainThreadWithResult(frame_range)
        if (start, end) != (int(sg_cut_in), int(sg_cut_out)):
            return u"当前文件帧范围为 {0} - {1}，与 shotgun 的帧范围 {2} - {3} 不一致，请找动画制片确认镜头时长".format(
                start, end, sg_cut_in, sg_cut_out)
        # 记录文件帧范围给 update_sg_version 更新 Version.frame_range / Shot cut 范围，
        # 它在 Dailies CLI（Maya 外）下也会跑，不能自己导 maya.cmds
        process_data['frame_range'] = [start, end]
    except:
        return traceback.format_exc()
