# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """记录资产面数,并更新到sg"""
    try:
        n_high = process_data.get("high", '|Root_grp|Geo_grp|high')
        auto_description = process_data.get("auto_description", {})
        mesh_cnt = 0
        for mesh in pm.listRelatives(n_high, ad=True, type='mesh'):
            mesh_cnt += mesh.numFaces()
        auto_description[u'高模面数'] = "{}".format(mesh_cnt)

    except Exception:
        return traceback.format_exc()
