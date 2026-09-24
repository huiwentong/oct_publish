# -*- coding: utf-8 -*-
import traceback

import pymel.core as pm
import maya.mel as mel
import maya.utils as utils

from publish_components.utils.sg_helper import get_asset_kind, DEFAULT_ASSET_TAG
from oct_maya.utils.maya_utils.shape import is_scene_has_instance


def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
    检查Freeze (旋转位移放缩 有没有归零)
    """
    try:
        def check():
            l_root_transforms = []
            l_geo_transforms = []
            n_root = process_data.get('root', '|Root_grp')
            n_geo = process_data.get('geo', '|Root_grp|Geo_grp')
            n_root = pm.PyNode(n_root)
            n_geo = pm.PyNode(n_geo)

            orig_trans = True
            for attr in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz']:
                if n_root.getAttr(attr) != 0:
                    orig_trans = False

            for attr in ['sx', 'sy', 'sz']:
                if n_root.getAttr(attr) != 1.0:
                    orig_trans = False

            if not orig_trans:
                # 存字符串，和下面的 l_geo_transforms 保持同一种类型
                l_root_transforms.append(n_root.name())

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

            l_geo_transforms = list(set(l_geo_transforms))
            return l_root_transforms, l_geo_transforms

        task_id = process_data['task_id']
        is_scene_asset = get_asset_kind(task_id) != DEFAULT_ASSET_TAG
        # 场景资产带关联复制时，instance 共享同一个 shape，坐标改不动，只有这种情况跳过；
        # 普通资产不管有没有关联复制都要查
        if not (is_scene_asset and is_scene_has_instance()):
            root_transforms, geo_transforms = utils.executeInMainThreadWithResult(check)
            if root_transforms or geo_transforms:
                process_data['check_freeze_l_geo_transforms'] = geo_transforms
                process_data['check_freeze_l_root_transforms'] = root_transforms
                return u"发现以下模型坐标未清零:\n{}".format(
                    '\n'.join(root_transforms + geo_transforms))

    except:
        return traceback.format_exc()

def fix(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
    检查Freeze (旋转位移放缩 有没有归零)
    """
    try:
        def _fix():
            l_geo_transforms = process_data.get('check_freeze_l_geo_transforms', [])
            l_root_transforms = process_data.get('check_freeze_l_root_transforms', [])

            for t in list(set(l_root_transforms)):
                logger.warning("AUTO FIX: 清理'{}'的模型坐标！".format(t))
                pm.lockNode(t, l=False)
                for attr in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz']:
                    pm.setAttr(t + '.' + attr, 0.0)
                for attr in ['sx', 'sy', 'sz']:
                    pm.setAttr(t + '.' + attr, 1.0)

            for t in list(set(l_geo_transforms)):
                logger.warning("AUTO FIX: 清理'{}'的模型坐标！".format(t))
                pm.lockNode(t, l=False)
                pm.select(t, r=True)
                mel.eval('FreezeTransformations;')

        utils.executeInMainThreadWithResult(_fix)

    except:
        return traceback.format_exc()