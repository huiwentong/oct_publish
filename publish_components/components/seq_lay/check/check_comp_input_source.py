# -*- coding: utf-8 -*-
import traceback

import maya.cmds as cmds
import maya.OpenMaya as om
import maya.utils as utils

from oct_maya.utils.maya_utils.pipe import list_ref_node


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    检查 reference 资产的输入连接只来自动画曲线、约束和动画层
    """
    # 迁自老工具 ani/check_comp_input_source（老配置允许跳过），测试时再决定去留。
    # 场次拆分到镜头时只保留动画曲线 / 约束，其他节点驱动 reference 里的 transform 会丢失效果。
    try:
        allowed_types = ['animCurveTL', 'animCurveTT', 'animCurveTU', 'animCurveTA', 'pointConstraint',
                         'parentConstraint', 'orientConstraint', 'animLayer', 'displayLayer', 'pairBlend']

        def check():
            errors = {}
            for ref_node in list_ref_node(loaded=True):
                # API 1.0 在 Python 里没有 MStringArray，直接传 list，Maya 会原地填入结果
                connections = []
                om.MFileIO.getReferenceConnectionsMade(cmds.referenceQuery(ref_node, filename=True), connections)
                # 结果成对出现：source, destination
                for i in range(0, len(connections) - 1, 2):
                    src, dst = connections[i], connections[i + 1]
                    if (cmds.objectType(src.split('.')[0]) not in allowed_types
                            and cmds.objectType(dst.split('.')[0]) == 'transform'):
                        errors.setdefault(ref_node, []).append('({0}, {1})'.format(src, dst))
            return errors

        errors = utils.executeInMainThreadWithResult(check)
        if errors:
            return u'文件内存在不正确的 ref 输入节点: \n' + '\n'.join(
                '{0}: {1}'.format(ref_node, ', '.join(cons)) for ref_node, cons in errors.items())
    except:
        return traceback.format_exc()
