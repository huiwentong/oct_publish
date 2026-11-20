# -*- coding: utf-8 -*-
import traceback

import maya.cmds as cmds
import maya.utils as utils

from oct.pipeline.task_context import TaskContext
from publish_components.utils.maya_utils import dialogs


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    检查文件帧范围与 SG 上镜头 cut in / cut out 一致
    """
    # 文件的播放范围应和 SG 上镜头的 cut in / cut out 一致；不一致时 GUI 下弹窗让用户确认，
    # 点“跳过检查”即以文件为准，update_sg_version 会把文件范围写回 SG。没有 GUI 不允许跳过。
    try:
        tc = TaskContext(process_data['task_id'])
        # TaskContext 进程内缓存，不刷新的话 SG 改了 cut in / out 重跑检查也拿不到
        tc.refresh()
        if tc.entity_type != 'Shot':
            return u"当前实体不是镜头：{0}".format(tc.entity_type)
        shot = tc.entity
        sg_ani_cut_in = shot.sg_ani_cut_in
        sg_ani_cut_out = shot.sg_ani_cut_out
        if sg_ani_cut_in is None or sg_ani_cut_out is None:
            return u"SG 上镜头 {0} 没有填写 cut in / cut out，请找制片确认".format(tc.entity_name)

        def frame_range():
            return (int(cmds.playbackOptions(q=True, min=True)),
                    int(cmds.playbackOptions(q=True, max=True)))

        start, end = utils.executeInMainThreadWithResult(frame_range)
        if (start, end) != (int(sg_ani_cut_in), int(sg_ani_cut_out)):
            msg = u"当前文件帧范围为 {0} - {1}，与 shotgun 的帧范围 {2} - {3} 不一致，请找动画制片确认镜头时长".format(
                start, end, sg_ani_cut_in, sg_ani_cut_out)
            if not parent_widget:
                return msg
            msg += u"\n如确认以文件范围为准，点“跳过检查”，提交后会把 SG 镜头范围更新为 {0} - {1}。".format(start, end)
            if dialogs.message_dialog("提示", msg, ["跳过检查", "停止提交"], parent=parent_widget) != "跳过检查":
                return msg
            if logger:
                logger.warning(u"用户确认跳过：镜头 {0} cut 范围将由 {1} - {2} 改为 {3} - {4}".format(
                    tc.entity_name, sg_ani_cut_in, sg_ani_cut_out, start, end))
        # 记录文件帧范围给 update_sg_version 更新 Version.frame_range / Shot cut 范围，
        # 它在 Dailies CLI（Maya 外）下也会跑，不能自己导 maya.cmds
        process_data['frame_range'] = [start, end]
    except:
        return traceback.format_exc()
