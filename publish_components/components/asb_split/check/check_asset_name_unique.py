# -*- coding: utf-8 -*-
import traceback

from oct.pipeline.shotgun.models import Asset
from oct.pipeline.task_context import TaskContext


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    检查同名资产的类型是否与本次拆分标记一致
    """
    # 同一项目内资产名唯一，已有 ASB/PROP 也不允许通过改标记切换类型。
    #
    # gen_asset_data 由 check_assembly_all_hierarchy 写入，本组件必须排在它之后。
    try:
        gen_asset_data = process_data.get('gen_asset_data')
        if not gen_asset_data:
            return u"没有拆分资产数据，请先通过 检查层级命名规范"

        # GUI 模式下 process_data 里没有 project_id，从 TaskContext 取。
        # 用 id 建过滤条件，避免 project_name 大小写不一致带来的问题
        tc = TaskContext(process_data['task_id']) or TaskContext.from_env()
        project = {'type': 'Project', 'id': tc.project_id}

        no_unique_asset_name_list = []
        for asset_name, asset_info in gen_asset_data.items():
            asset_type = asset_info['asset_type']
            if asset_type not in ('ASB', 'PROP'):
                return u"资产 {0} 的拆分类型不支持: {1}".format(asset_name, asset_type)
            filters = [
                ['code', 'is', asset_name],
                ['project', 'is', project],
            ]
            # 查全量同名资产，避免类型过滤隐藏另一类型下的同名记录。
            for sg_asset in Asset.filter(filters=filters):
                if sg_asset.sg_asset_type != asset_type:
                    no_unique_asset_name_list.append(
                        '{0}: SG类型={1}, 本次标记={2}'.format(
                            asset_name, sg_asset.sg_asset_type, asset_type))

        if no_unique_asset_name_list:
            return u"以下资产类型与SG已有记录冲突，请恢复标记或使用新名称: {0}".format(
                u", ".join(no_unique_asset_name_list))

    except:
        return traceback.format_exc()
