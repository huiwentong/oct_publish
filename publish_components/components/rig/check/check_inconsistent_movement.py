#!/usr/bin/env python  
# -*- coding:utf-8 -*-

import traceback


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
检查不统一的移动效果
    """
    import maya.cmds as mc
    import math

    a = math.sqrt(2)
    try:
        if mc.ls(type='AlembicNode'):
            return ""

        mc.autoKeyframe(state=False)

        mesh_list = mc.listRelatives('high', c=1, ad=1, type='mesh', noIntermediate=1)
        mesh_list = [mc.listRelatives(mesh, p=1)[0] for mesh in mesh_list if
                     not mc.getAttr(mesh + ".intermediateObject")]

        default_bbx = mc.polyEvaluate(mesh_list, b=1)
        center_offset = [default_bbx[i][1] - default_bbx[i][0] for i in range(3)]
        root_ctrl = 'master_ctrl'
        for i in [10, 20, 30]:
            mc.setAttr(root_ctrl + '.translateX', i)
            bbx = mc.polyEvaluate(mesh_list, b=1)
            offset = [bbx[i][1] - bbx[i][0] for i in range(3)]
            distance = math.sqrt(math.pow(offset[0] - center_offset[0], 2) +
                                 math.pow(offset[1] - center_offset[1], 2) +
                                 math.pow(offset[2] - center_offset[2], 2))
            # 保留两位小数
            distance = round(distance, 2)

            if distance > 0.001:
                mc.setAttr(root_ctrl + '.translateX', 0)
                return u"移动大环时不是所有物体都正确位移，请检查。"

        mc.setAttr(root_ctrl + '.translateX', 0)
        return ""

    except:
        return traceback.format_exc()


