# -*- coding: utf-8 -*-
import traceback
import random
import pymel.core as pm
import maya.mel as mel
import maya.utils as utils


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查 UV Set，确保第一个且唯一的 UV Set 为 map1"""
    try:
        def check():
            n_high = process_data.get("high", "|Root_grp|Geo_grp|high")

            return [
                mesh.longName()
                for mesh in pm.listRelatives(n_high, ad=True, type="mesh", ni=True, fullPath=True)
                if (pm.polyUVSet(mesh, q=True, allUVSets=True) or []) != ["map1"]
            ]

        error_nodes = utils.executeInMainThreadWithResult(check)
        if error_nodes:
            process_data["uv_set_error_nodes"] = error_nodes
            return "以下模型 UV Set 不正确:\n{}".format("\n".join(error_nodes))

    except Exception:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """修复 UV Set，确保第一个且唯一的 UV Set 为 map1"""
    try:
        def repair():
            error_nodes = process_data.get("uv_set_error_nodes", [])
            for mesh in error_nodes:
                uv_sets = pm.polyUVSet(mesh, q=True, allUVSets=True) or []

                # 处理重复 map1
                if uv_sets.count("map1") > 1:
                    for _ in range(uv_sets.count("map1")):
                        new_name = "map1_{}".format(str(random.random())[2:])
                        pm.polyUVSet(mesh, uvSet="map1", rename=True, newUVSet=new_name)

                # 保证第一个 UV Set 最终可以命名为 map1
                j = 0
                while True:
                    uv_sets = pm.polyUVSet(mesh, q=True, allUVSets=True) or []
                    if "map1" not in uv_sets:
                        break

                    pm.polyUVSet(mesh, uvSet="map1", currentUVSet=True)
                    if uv_sets.index("map1") != 0:
                        pm.polyAutoProjection(mesh, ch=False)
                        new_name = "map1_{}".format(str(random.random())[2:])
                        pm.polyUVSet(mesh, uvSet="map1", rename=True, newUVSet=new_name)
                    else:
                        break

                    j += 1
                    if j > 100:
                        break

                uv_sets = pm.polyUVSet(mesh, q=True, allUVSets=True) or []

                if not uv_sets:
                    pm.polyUVSet(mesh, uvSet="map1", create=True)

                elif uv_sets[0] != "map1":
                    pm.polyUVSet(mesh, uvSet=uv_sets[0], rename=True, newUVSet="map1")

                # 检查 map1 是否有 UV
                uv_sets = pm.polyUVSet(mesh, q=True, allUVSets=True) or []
                pm.polyUVSet(mesh, uvSet="map1", currentUVSet=True)

                if pm.polyEvaluate(mesh, uvcoord=True) == 0:
                    valid_uv = None

                    for uv_set in uv_sets:
                        if uv_set == "map1":
                            continue

                        pm.polyUVSet(mesh, uvSet=uv_set, currentUVSet=True)
                        if pm.polyEvaluate(mesh, uvcoord=True):
                            valid_uv = uv_set
                            break

                    if valid_uv:
                        pm.polyUVSet(mesh, uvSet=valid_uv, copy=True, newUVSet="map1")
                    else:
                        pm.polyUVSet(mesh, uvSet="map1", currentUVSet=True)
                        pm.polyAutoProjection(mesh, ch=False)

                # 删除 map1 之外的 UV Set
                uv_sets = pm.polyUVSet(mesh, q=True, allUVSets=True) or []
                for uv_set in uv_sets[1:]:
                    pm.polyUVSet(mesh, uvSet=uv_set, delete=True)

                pm.polyUVSet(mesh, uvSet="map1", currentUVSet=True)
                pm.select(mesh, r=True)
                mel.eval("DeleteHistory")
                logger.warning( "AUTO FIX: 修复 '{}' 节点的 UV Set".format(mesh))
            pm.select(clear=True)

        utils.executeInMainThreadWithResult(repair)

    except Exception:
        return traceback.format_exc()
