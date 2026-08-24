# -*- coding: utf-8 -*-
import traceback, os
import pymel.core as pm
from importlib import reload
from publish_components.utils.maya_utils import get_upstream_nodes
reload(get_upstream_nodes)

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查资产 Shader 上中丢失的贴图"""
    try:
        def get_error_tex(asset_tex):
            errors = []
            for f in asset_tex:
                if f.nodeType() == 'file':
                    f_path = pm.getAttr(f + '.fileTextureName')
                    if not os.path.isfile(f_path):
                        errors.append(f.nodeName() + ' ' + f_path)

                if f.nodeType() == 'aiImage':
                    f_path = pm.getAttr(f + '.filename')
                    if not os.path.isfile(f_path):
                        errors.append(f.nodeName() + ' ' + f_path)

            return errors

        l_asset_tex = []
        n_root = process_data.get('root', '|Root_grp')
        n_root = pm.PyNode(n_root)
        root_fullpath = [n_root.longName() + "|"]
        for se in pm.ls(type='shadingEngine'):
            l_tex = []
            asset_se = False
            for node_path in get_upstream_nodes.get_nodes(se):
                n = pm.PyNode(node_path)
                for root in root_fullpath:
                    if node_path.startswith(root):
                        asset_se = True
                if n.nodeType() in ['file', 'aiImage']:
                    l_tex.append(n)

            if asset_se:
                l_asset_tex.extend(l_tex)
        l_errors = get_error_tex(l_asset_tex)
        if l_errors:
            return u'资产贴图丢失：\n' + '\n'.join(l_errors)
    except Exception:
        return traceback.format_exc()
