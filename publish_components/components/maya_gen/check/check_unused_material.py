# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.utils as utils
def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查 Maya 文件中多余的材质并删除"""
    try:
        def flat(list_):
            res = []
            for i in list_:
                if isinstance(i, list):
                    res.extend(flat(i))
                else:
                    res.append(i)
            return res

        all_se = pm.ls(type='shadingEngine')
        all_needed_meterials_temp = [pm.listConnections(each, s=1, d=0) for each in all_se]
        all_needed_meterials = list(set(flat(all_needed_meterials_temp)))
        all_materials = utils.executeInMainThreadWithResult(lambda :pm.ls(mat=1))
        all_useless_materials = [every for every in all_materials if every not in all_needed_meterials]
        if int(pm.about(version=1)) >= 2020:
            if 'standardSurface1' in all_useless_materials:
                all_useless_materials.remove('standardSurface1')
        if all_useless_materials:
            logger.warning("AUTO FIX: 删除以下未被使用的材质节点：".format("\n".join(all_useless_materials)))

    except Exception:
        return traceback.format_exc()
