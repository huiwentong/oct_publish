# -*- coding:utf-8 -*-

import traceback


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    def run_check():
        import pymel.core as pm
        global pm

        try:

            l_bad_names = []
            for asset_name, asset_info in self.dialog.d_assets_info.items():
                root = asset_info['high']
                for n_mesh in pm.listRelatives(root, ad=True, type='mesh'):
                    if n_mesh.isIntermediateObject():
                        trans_node = n_mesh.getParent()
                        trans_name = trans_node.nodeName()
                        if n_mesh.nodeName() == trans_name + 'Shape':
                            l_bad_names.append(n_mesh.nodeName())

            if len(l_bad_names) > 0:
                return u'Intermediate Object mesh 节点名不能由 transform + Shape 构成的：' + ', '.join(l_bad_names)

            return ""

        except:
            return traceback.format_exc()

    def run_fix():
        '''Auto Fix'''
        try:
            for asset_name, asset_info in self.dialog.d_assets_info.items():
                root = asset_info['high']
                for n_mesh in pm.listRelatives(root, ad=True, type='mesh'):
                    if n_mesh.isIntermediateObject():
                        trans_node = n_mesh.getParent()
                        trans_name = trans_node.nodeName()
                        if n_mesh.nodeName() == trans_name + 'Shape':
                            n_mesh.rename(trans_name + 'ShapeOrig')

            return ''

        except:
            return traceback.format_exc()

    check_result = run_check()
    if check_result:
        run_fix()



