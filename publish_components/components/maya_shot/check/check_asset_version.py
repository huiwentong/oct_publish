# -*- coding: utf-8 -*-
import traceback

import maya.utils as utils

from oct_maya.utils.maya_utils import pipe


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    检查引用的资产是否都使用无版本号的版本文件
    """
    # 老 lay/check_asset_version。老 runlist 里允许跳过，新架构按硬性阻断。
    try:
        def check():
            comp_info = pipe.ShotDataGenerator().generate_comp_info()
            return [info['component_node'] for comp, info in comp_info.items()
                    if info['type'] == 'reference' and info['with_version_num']]

        l_error_assets = utils.executeInMainThreadWithResult(check)
        if l_error_assets:
            return u'以下资产没有使用无版本号版本: {0}'.format(', '.join(l_error_assets))
    except:
        return traceback.format_exc()
