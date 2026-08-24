# -*- coding: utf-8 -*-
import traceback
import os
from pxr import Usd
from glob import glob
import pymel.core as pm
from importlib import reload
from oct.data.usd import step_pub_usds
from oct.pipeline.path_acs import make_dirs
from publish_components.utils.sg_helper import is_rig_task_omit
from oct_maya.utils.maya_utils.shape import is_scene_has_instance
from publish_components.utils.maya_utils.export_usd_core import batch_export_usd
reload(step_pub_usds)

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """导出资产的版本 USD 文件"""

    try:

        task_id = process_data.get("task_id")
        v_dir_usd = process_data["v_dir_usd"]
        version_dir = process_data["version_dir"]
        n_low = process_data.get("low", "|Root_grp|Geo_grp|low")
        is_env = is_rig_task_omit(task_id)
        pm.loadPlugin('mayaUsdPlugin', quiet=True)

        # 如果它的绑定任务状态为弃用，代表它是一个场景
        # 场景如果带有关联复制，无法导出usd，需要设置导出usd参数 exportInstances=False
        if is_env and is_scene_has_instance():
            export_instances_value = False
        else:
            export_instances_value = True

        if not os.path.exists(v_dir_usd):
            make_dirs(v_dir_usd)

        args = {
            "exportRoots": ["|Root_grp|Geo_grp"],
            "exportUVs": True,
            "exportSkels": "none",
            "exportSkin": "none",
            "exportBlendShapes": False,
            "exportColorSets": True,
            "defaultMeshScheme": "none",
            "defaultUSDFormat": "usdc",
            "eulerFilter": False,
            "staticSingleSample": False,
            "frameStride": 1,
            "frameSample": 0.0,
            "parentScope": "",
            "exportDisplayColor": False,
            "shadingMode": "useRegistry",
            "convertMaterialsTo": "UsdPreviewSurface",
            "exportInstances": export_instances_value,
            "exportVisibility": True,
            "mergeTransformAndShape": False,
            "stripNamespaces": True,
        }

        maya_file = glob(version_dir + '/*.ma')[0].replace('\\', '/')
        batch_export_usd(maya_file, v_dir_usd + '/high.usd', **args)
        Usd.Stage.Open(v_dir_usd + '/high.usd')

        has_low = False
        if is_env and pm.objExists(n_low):
            has_low = bool(pm.listRelatives(n_low, allDescendents=True, shapes=True))
        step_pub_usds.ModStepUsd(version_folder=version_dir,task_id=task_id, has_low=has_low)


    except Exception:
        return traceback.format_exc()
