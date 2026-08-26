#!/usr/bin/env python  
# -*- coding:utf-8 -*-
""" 
@author:jiongwan
@team : Octmedia TD Department
@file: check_display_override.py
@time: 2022/08/12
@contact: wanjw126@126.com
"""
import traceback


# All system check classes will use StdCheck as the class name.
class StdCheck():

    def __init__(self, dialog):
        self.dialog = dialog
        self.check_name = u"检查high组下dag节点的overrideEnabled属性"
        self.description = u"所有dag节点的overrideEnabled属性都应该设置为disabled"
        self.auto_fix = True
        self.duty = u"艺术家本人。"

        self.error_node_list = []
        return

    def run_check(self):
        import pymel.core as pm
        global pm
        try:
            self.error_node_list = []

            for asset_name, asset_info in self.dialog.d_assets_info.items():
                n_high = asset_info['geo']
                l_nodes = pm.listRelatives(n_high, ad=True)
                for node in l_nodes:
                    if pm.objExists(node + '.overrideEnabled'):
                        override_enabled = pm.getAttr(node + '.overrideEnabled')
                        if override_enabled:
                            self.error_node_list.append(node.name())

            if len(self.error_node_list) > 0:
                return u'发现以下节点的overrideEnabled属性打开了:\n{}。\n'.format('; '.join(self.error_node_list))

            return ""

        except:
            return traceback.format_exc()

    def run_fix(self):
        '''Auto Fix'''
        try:
            for node in self.error_node_list:
                pm.setAttr(node+'.overrideEnabled', l=0)
                pm.setAttr(node + '.overrideEnabled', False)

            return ''
        except:
            return traceback.format_exc()

    def get_check_name(self):
        return self.check_name

    def get_description(self):
        return self.description

    def get_auto_fix(self):
        return self.auto_fix

    def get_duty(self):
        return self.duty
