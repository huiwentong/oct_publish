#!/usr/bin/env python  
# -*- coding:utf-8 -*-
""" 
@author:jiongwan
@team : Octmedia TD Department
@file: check_rig_hierarchy_nzt.py
@time: 2022/07/27
@contact: wanjw126@126.com
"""
import traceback

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
检查绑定层级
    """

    print("=== check_rig_hierarchy ===")
    print("=== process_data ===")
    print(process_data)
    # n_root = process_data.get("root")

    def run_check():

        import pymel.core as pm

        try:
            asset_info = self.dialog.d_assets_info[self.dialog.entity['code']]
            n_root = asset_info['root']
            n_geo = asset_info['geo']

            if not pm.objExists('|Root_grp|Rig_grp'):
                return u"Root 组下没有 Rig_grp。"

            for c in pm.listRelatives(n_root, c=True):
                if c.nodeName() not in [n_geo.name(), 'Rig_grp']:
                    return u"Root 组下应该只有 Geo_grp 和 Rig_grp，现在有了 {} 。".format(c.nodeName())

            for ctrl in [self.dialog.root_ctrl, self.dialog.main_ctrl, self.dialog.vis_ctrl]:
                if not pm.objExists(ctrl):
                    return u'缺少 {}!'.format(ctrl)

                if ctrl != self.dialog.vis_ctrl:
                    if not pm.objExists(ctrl + '_SN') or not pm.objExists(ctrl + '_PH'):
                        return u'绑定中应该有{0}_SN, {0}_PH'.format(ctrl)

            return ""

        except:
            return traceback.format_exc()

