# -*- coding: utf-8 -*-
import traceback

import pymel.core as pm
import maya.utils as utils

from oct.pipeline.task_context import TaskContext


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    检查 cam 组下的相机名：必须是 <镜头名>_cam
    """
    # 只处理 Shot 实体。相机 shape 名和 transform 名不匹配时会顺手改成 <transform>Shape。
    try:
        tc = TaskContext(process_data['task_id'])
        if tc.entity_type != 'Shot':
            return u"当前实体不是镜头：{0}".format(tc.entity_type)
        l_valid_names = [tc.entity_name + '_cam']

        def check():
            if not pm.objExists('|cam'):
                return u"没有 |cam 组"

            cams = pm.listRelatives('|cam', ad=True, type='camera')
            if not cams:
                return u"|cam 下面没有相机"

            l_invalid_names = []
            d_shot_cams = {}
            for cam in cams:
                cam_p = cam.getParent()
                if cam_p.getParent().longName() != '|cam':
                    return u"相机必须直接位于 |cam 组下：{0}".format(cam_p.longName())
                if cam.nodeName() != cam_p.nodeName() + 'Shape':
                    cam.rename(cam_p.nodeName() + 'Shape')
                    logger.warning(u"AUTO FIX: 相机 shape 改名为 {0}".format(cam_p.nodeName() + 'Shape'))

                if cam_p.nodeName() not in l_valid_names:
                    l_invalid_names.append(cam_p.nodeName())
                else:
                    shot_name = cam_p.nodeName().split('_')[0]
                    d_shot_cams.setdefault(shot_name, []).append(cam_p.name())

            if l_invalid_names:
                return u"|cam 组下有非镜头使用的相机：{0}，相机名必须是 {1}".format(
                    ' '.join(l_invalid_names), ' / '.join(l_valid_names))

            for shot_name, l_cam in d_shot_cams.items():
                if len(l_cam) > 1:
                    return u"有镜头相关相机超过 1 个: " + ' '.join(l_cam)
            return ""

        result = utils.executeInMainThreadWithResult(check)
        if result:
            return result
    except:
        return traceback.format_exc()
