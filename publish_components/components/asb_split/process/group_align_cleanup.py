# -*- coding: utf-8 -*-
import traceback

import maya.cmds as cmds
import pymel.core as pm

from oct_maya.utils.maya_utils.transform import set_pivot_to_world_origin_and_freeze


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    轴心对齐世界原点，冻结属性
    """
    # 将组轴心对齐世界原点并冻结变换，物体本身的世界位置保持不变。
    # 仅农场端使用。
    try:
        # 主 ASB 不需要移动到轴心原点
        if process_data.get('is_main_asb_asset'):
            logger.info(u"主 ASB 资产，跳过轴心对齐")
            return

        # PROP 处理的是 standard_structure 生成的 |Root_grp|Geo_grp|high，
        # 子 ASB 处理资产根节点本身
        root_node = process_data['root']
        if cmds.objExists('|Root_grp|Geo_grp|high'):
            root_node = pm.PyNode('|Root_grp|Geo_grp|high')

        logger.info(u"轴心对齐: {0}".format(root_node.longName()))
        set_pivot_to_world_origin_and_freeze(long_name=root_node.longName())

    except:
        return traceback.format_exc()
