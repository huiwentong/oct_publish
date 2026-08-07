# -*- coding:utf-8 -*-
"""
===========================================
项目名称: int
文件: efx_gener_usd_file
作者: huiwentong
创建时间: 2026/1/12
版本: 1.0.0
联系方式: 1120267329@qq.com
描述:
    ******
===========================================
"""

import traceback

from oct.data.usd import step_pub_usds




def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
生成 shot USD文件
    """
    try:
        v_comp_dir = process_data['version_dir'] + '/components'
        comp_dict = {}
        for k, v in submit_data['components'].items():
            comp_node = v['cache_node']
            comp_type = v['cache_type']
            visible = True
            if comp_type == "禁用":
                visible = False
            tar_path = f'/world/efx/{k}'
            usd_file = comp_path = v_comp_dir+f'/{k}/comp.usda'
            comp_dict[tar_path] = {
                'usd_file': usd_file,
                'usd_path': tar_path,
                'transform': None,
                'visible': visible,
            }
        step_pub_usds.EfxStepUsd(process_data['version_dir'], process_data['task_id'], comp_dict)
    except:
        return traceback.format_exc()
