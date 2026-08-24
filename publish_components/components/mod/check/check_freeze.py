# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.mel as mel
import maya.utils as utils
def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
    检查Freeze (旋转位移放缩 有没有归零)
    """
    try:
        l_root_transforms = []
        l_geo_transforms = []
        n_root = process_data.get('root', '|Root_grp')
        n_root = pm.PyNode(n_root)

        orig_trans = True
        for attr in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz']:
            if n_root.getAttr(attr) != 0:
                orig_trans = False

        for attr in ['sx', 'sy', 'sz']:
            if n_root.getAttr(attr) != 1.0:
                orig_trans = False

        if not orig_trans:
            l_root_transforms.append(n_root.name())

        n_geo = process_data.get('geo', '|Root_grp|Geo_grp')
        n_geo = pm.PyNode(n_geo)

        l_transforms = pm.listRelatives(n_geo, ad=True, type='transform', path=True)
        l_transforms.append(n_geo)

        for each in l_transforms:
            if '|misc|' in each.fullPath():
                continue
            for attr in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz']:
                if each.getAttr(attr) != 0:
                    l_geo_transforms.append(each.name())

            for attr in ['sx', 'sy', 'sz']:
                if each.getAttr(attr) != 1.0:
                    l_geo_transforms.append(each.name())

        for t in list(set(l_root_transforms)):
            logger.warning("清理'{}'的模型坐标！".format(t))
            pm.lockNode(t, l=False)
            for attr in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz']:
                pm.setAttr(t + '.' + attr, 0.0)
            for attr in ['sx', 'sy', 'sz']:
                pm.setAttr(t + '.' + attr, 1.0)

        for t in list(set(l_geo_transforms)):
            pm.lockNode(t, l=False)
            pm.select(t, r=True)
            utils.executeInMainThreadWithResult(lambda: mel.eval('FreezeTransformations;'))
    except:
        return traceback.format_exc()