# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """关闭节点的verrideEnabled属性"""
    try:
        n_geo = process_data.get("geo", "|Root_grp|Geo_grp")
        l_nodes = pm.listRelatives(n_geo, ad=True)
        for node in l_nodes:
            if pm.objExists(node + '.overrideEnabled'):
                override_enabled = pm.getAttr(node + '.overrideEnabled')
                if override_enabled:
                    logger.warning("AUTO FIX：关闭节点'{}'的 overrideEnabled 属性！".format(str(node)))
                    pm.setAttr(node + '.overrideEnabled', l=0)
                    pm.setAttr(node + '.overrideEnabled', False)

    except Exception:
        return traceback.format_exc()
