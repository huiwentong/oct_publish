# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.utils as utils

def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
    检查按面赋材质
    """
    try:
        def check():
            l_bad_meshes = []
            n_high = process_data.get('high', '|Root_grp|Geo_grp|high')
            for mesh in pm.listRelatives(n_high, ad=True, type='mesh'):
                l_se = pm.listConnections(mesh, d=True, s=False, type='shadingEngine')
                if l_se:
                    l_se_names = [n.name() for n in l_se]
                    l_se_names = list(set(l_se_names))
                    if len(l_se_names) > 1:
                        l_bad_meshes.append(mesh.name())
            return l_bad_meshes
        bad_meshes = utils.executeInMainThreadWithResult(check)
        if len(bad_meshes) > 0:
            return u"以下的面有按面赋材质的情况：\n" + '\n'.join(bad_meshes)
    except:
        return traceback.format_exc()


