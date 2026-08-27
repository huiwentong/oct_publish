#!/usr/bin/env python  
# -*- coding:utf-8 -*-

import traceback
import math
import maya.cmds as mc
import maya.utils as utils


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
检查不统一的移动效果
    """
    try:
        def process():
            if mc.ls(type='AlembicNode'):
                return ""
            mc.autoKeyframe(state=False)

            # 确定mesh列表
            mesh_list = mc.listRelatives('high', c=1, ad=1, type='mesh', noIntermediate=1)
            mesh_list = [mc.listRelatives(mesh, p=1)[0] for mesh in mesh_list if
                         not mc.getAttr(mesh + ".intermediateObject")]

            # 先将主控制器归零
            root_ctrl = 'master_ctrl'
            mc.setAttr(root_ctrl + '.translateX', 0)
            default_bbx = mc.polyEvaluate(mesh_list, b=1)
            center_offset = [(default_bbx[i][1] + default_bbx[i][0]) / 2 for i in range(3)]

            # 将物体移动其自身的一个 x 向的尺寸，确认包围盒中心的位移是否与该数值一致
            movement_x = default_bbx[0][1] - default_bbx[0][0]
            mc.setAttr(root_ctrl + '.translateX', movement_x)
            bbx = mc.polyEvaluate(mesh_list, b=1)
            offset = [(bbx[i][1] + bbx[i][0]) / 2 for i in range(3)]
            distance = math.sqrt(math.pow(offset[0] - center_offset[0], 2) +
                                 math.pow(offset[1] - center_offset[1], 2) +
                                 math.pow(offset[2] - center_offset[2], 2))
            if abs(distance - movement_x) > 0.001:
                mc.setAttr(root_ctrl + '.translateX', 0)
                return u"移动大环时不是所有物体都正确位移，请检查。"

            mc.setAttr(root_ctrl + '.translateX', 0)
            return ""

        return utils.executeInMainThreadWithResult(process)


    except:
        return traceback.format_exc()
