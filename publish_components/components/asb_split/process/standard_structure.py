# -*- coding: utf-8 -*-
import traceback

import pymel.core as pm


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    为不同类型资产，整理场景为标准结构
    """
    # PROP 整理成 |Root_grp|Geo_grp|high，ASB 保持自身层级命名。
    #
    # 仅农场端（run_asb_deadline_job_new.py）使用，不进 GUI 的 runlist：
    # 它会改场景层级结构，只在 mayapy standalone 里对拆出来的单个子资产执行。
    try:
        entity_name = process_data['entity_name']
        asset_type = process_data['entity_asset_type']

        root_node = process_data['root']

        # 如果 root 不在最外层，则提出到最外层
        if root_node.getParent():
            pm.parent(root_node, world=True)

        # 如果为 PROP 类型，放在 |Root_grp|Geo_grp 下
        if asset_type == 'PROP':
            # 改名为 high
            root_node.rename('high')

            if not pm.objExists('|Root_grp'):
                root_grp = pm.createNode('transform', name='Root_grp')
            else:
                root_grp = pm.PyNode('|Root_grp')

            if not pm.objExists('|Root_grp|Geo_grp'):
                geo_grp = pm.createNode('transform', name='Geo_grp', parent=root_grp)
            else:
                geo_grp = pm.PyNode('|Root_grp|Geo_grp')

            pm.parent(root_node, geo_grp)

            # 重新指定 root，后续组件都读这个键
            process_data['root'] = root_grp
            root_node = root_grp

        # 删除多余的顶层 group
        for obj in pm.ls(assemblies=True):
            if not pm.ls(obj, dag=True, type='mesh'):
                continue
            if obj.longName() != root_node.longName():
                pm.delete(obj)

        logger.info(u"{0} ({1}) 已整理为标准结构，root: {2}".format(
            entity_name, asset_type, root_node.longName()))

    except:
        return traceback.format_exc()
