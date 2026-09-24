# -*- coding: utf-8 -*-
import traceback

import maya.cmds as cmds
import maya.mel as mel
import pymel.core as pm

from oct_maya.utils.maya_utils.shape import is_scene_has_instance
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

        # instance 的多个 transform 共享同一份 shape 顶点数据，freeze 是把变换烘进顶点，
        # 烘一次所有副本都会跟着动，Maya 本身也拒绝对 instanced object 执行。
        # 这里静默跳过继续发布，代价是该子资产的变换通道不为零
        if is_scene_has_instance():
            logger.warning(u"场景含关联复制，跳过轴心对齐和 freeze: {0}".format(
                root_node.longName()))
            return

        logger.info(u"轴心对齐: {0}".format(root_node.longName()))
        set_pivot_to_world_origin_and_freeze(long_name=root_node.longName())

        # 根节点对齐后，子层级组自身的变换还在，逐个 freeze。
        # 形状照抄 mod/check/check_freeze.py 的 fix()：解锁 -> 选中 -> FreezeTransformations，
        # 不对父组调 makeIdentity（那样变换会向下传递，容易重复应用）。
        targets = pm.listRelatives(root_node, ad=True, type='transform', path=True) or []
        for t in targets:
            pm.lockNode(t, l=False)
            pm.select(t, r=True)
            mel.eval('FreezeTransformations;')
        pm.select(clear=True)
        logger.info(u"逐个 freeze 完成，共 {0} 个子层级节点".format(len(targets)))

    except:
        return traceback.format_exc()
