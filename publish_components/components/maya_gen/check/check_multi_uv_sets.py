# -*- coding: utf-8 -*-
import traceback
import maya.mel as mel
import random
import pymel.core as pm
import maya.utils as utils


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查并修复 UV Set，确保每个 mesh 只有 map1"""

    try:
        def fix(meshs):
            for m in meshs:
                logger.warning("AUTO FIX: 修复 '{}'节点的多个 UV Set".format(str(m)))
                l_uv_sets = pm.polyUVSet(m, q=True, allUVSets=True)
                if l_uv_sets.count('map1') > 1:
                    count = l_uv_sets.count('map1')
                    for i in range(count):
                        new_name = 'map1_{}'.format(str(random.random())[2:])
                        pm.polyUVSet(m, uvSet='map1', rename=True, newUVSet=new_name)
                j = 0
                while 1:
                    l_uv_sets = pm.polyUVSet(m, q=True, allUVSets=True)
                    if 'map1' in l_uv_sets:
                        pm.polyUVSet(m, uvSet='map1', currentUVSet=1)
                        if l_uv_sets.index('map1') != 0:
                            pm.polyAutoProjection(m, ch=0)
                            new_name = 'map1_{}'.format(str(random.random())[2:])
                            pm.polyUVSet(m, uvSet='map1', rename=True, newUVSet=new_name)
                    else:
                        break

                    j = j + 1
                    if j > 100:
                        break

                l_uv_sets = pm.polyUVSet(m, q=True, allUVSets=True)
                for i in range(len(l_uv_sets)):
                    if i == 0:
                        if l_uv_sets[0] != 'map1':
                            pm.polyUVSet(m, uvSet=l_uv_sets[0], rename=True, newUVSet='map1')

                l_uv_sets = pm.polyUVSet(m, q=True, allUVSets=True)
                pm.polyUVSet(m, uvSet='map1', currentUVSet=1)
                uv_cnt = pm.polyEvaluate(m, uvcoord=1)
                vaild_uv_name = ''
                if uv_cnt == 0:
                    for uv_set_name in l_uv_sets:
                        if uv_set_name == 'map1':
                            continue
                        pm.polyUVSet(m, uvSet=uv_set_name, currentUVSet=1)
                        uv_cnt = pm.polyEvaluate(m, uvcoord=1)
                        if uv_cnt != 0:
                            vaild_uv_name = uv_set_name
                            pm.polyUVSet(m, uvSet=vaild_uv_name, copy=True, newUVSet='map1')
                            break
                    if not vaild_uv_name:
                        pm.polyUVSet(m, uvSet='map1', currentUVSet=1)
                        pm.polyAutoProjection(m, ch=0)

                for i in range(1, len(l_uv_sets)):
                    pm.polyUVSet(m, uvSet=l_uv_sets[i], delete=True)
                pm.select(m, r=1)
                mel.eval('DeleteHistory')
            pm.select(cl=1)

        n_high = process_data.get("high", "|Root_grp|Geo_grp|high")

        l_bad_meshes = []
        for mesh in pm.listRelatives(n_high, ad=True, type="mesh", ni=True, fullPath=True):
            l_uv_sets = pm.polyUVSet(mesh, q=True, allUVSets=True)
            if not l_uv_sets:
                pm.polyUVSet(mesh, uvSet='map1', create=True)
            if len(l_uv_sets) == 1:
                uv_set_name = l_uv_sets[0]
                if uv_set_name != 'map1':
                    pm.polyUVSet(mesh, uvSet=uv_set_name, rename=True, newUVSet='map1')
            elif len(l_uv_sets) == 0:
                pm.polyUVSet(mesh, uvSet='map1', create=True)
            else:
                l_bad_meshes.append(mesh.name())

        utils.executeInMainThreadWithResult(fix, l_bad_meshes)

    except Exception:
        return traceback.format_exc()
