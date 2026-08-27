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
import pymel.core as pm
import maya.utils as utils


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
检查绑定层级
    """
    try:
        def process():
            n_root = process_data.get("root", '|Root_grp')
            n_root = pm.PyNode(n_root)
            n_geo = process_data.get("geo", '|Root_grp|Geo_grp')
            n_geo = pm.PyNode(n_geo)

            if not pm.objExists('|Root_grp|Rig_grp'):
                return u"Root 组下没有 Rig_grp。"

            for c in pm.listRelatives(n_root, c=True):
                if c.nodeName() not in [n_geo.name(), 'Rig_grp']:
                    return u"Root 组下应该只有 Geo_grp 和 Rig_grp，现在有了 {} 。".format(c.nodeName())

            if not pm.objExists('|root_jnt'):
                return u'世界下没有root_jnt'

            if pm.objExists('master_ctrl.displayType'):
                if pm.getAttr('master_ctrl.displayType') != 2:
                    return u'master_ctrl的displayType属性要设置为reference'

                return ""

        return utils.executeInMainThreadWithResult(process)

    except Exception:
        return traceback.format_exc()
