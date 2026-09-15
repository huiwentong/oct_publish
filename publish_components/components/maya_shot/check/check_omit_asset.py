# -*- coding: utf-8 -*-
import traceback

import maya.utils as utils

from oct.pipeline.shotgun.models import Asset
from oct.pipeline.task_context import TaskContext
from oct_maya.utils.maya_utils import pipe


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    检查有没有已经 Omit 的资产还在场景中调用
    """
    # 场景里引用了 SG 上已 Omit 的资产时报错，需要 unload 或换成正确的资产。
    try:
        tc = TaskContext(process_data['task_id'])
        project = {'type': 'Project', 'id': tc.project_id}

        def collect_assets():
            comp_info = pipe.ShotDataGenerator().generate_comp_info()
            d_asset_nodes = {}
            for comp, info in comp_info.items():
                d_asset_nodes.setdefault(info['asset_name'], []).append(info['component_node'])
            return d_asset_nodes

        d_asset_nodes = utils.executeInMainThreadWithResult(collect_assets)

        # 一次查完，避免每个资产都打一次 SG
        # 成功时不能 return —— CLI 模式下所有组件的 main() 会被平铺进同一个函数
        sg_assets = {}
        if d_asset_nodes:
            for asset in Asset.filter(filters=[['project', 'is', project],
                                               ['code', 'in', list(d_asset_nodes.keys())]],
                                      fields=['code', 'sg_status_list']):
                sg_assets[asset.code] = asset.sg_status_list

        l_omit_assets = []
        for a_name, l_a_nodes in d_asset_nodes.items():
            status = sg_assets.get(a_name)
            if status is None or status == 'omt':
                l_omit_assets.append('{0}: {1}'.format(a_name, ' '.join(l_a_nodes)))

        if l_omit_assets:
            return u"发现 omit 或者无法在 shotgun 上追踪的资产:\n" + '\n'.join(l_omit_assets)
    except:
        return traceback.format_exc()
