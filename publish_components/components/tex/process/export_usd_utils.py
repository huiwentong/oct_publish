# -*- coding: utf-8 -*-
import traceback
import os
import glob
from pxr import Usd
import pymel.core as pm
from importlib import reload
from oct.data.usd import step_pub_usds
from oct.pipeline.path_acs import make_dirs
from publish_components.utils.maya_utils.export_usd_core import batch_export_tex_usd
reload(step_pub_usds)

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """导出 tex USD 文件"""

    try:

        task_id = process_data.get("task_id")
        v_dir_usd = process_data["v_dir_usd"]
        version_dir = process_data["version_dir"]
        publish_type = process_data.get("publish_type", "Publish")
        pm.loadPlugin('mayaUsdPlugin', quiet=True)

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
            "exportInstances": True,
            "exportVisibility": True,
            "mergeTransformAndShape": False,
            "stripNamespaces": True,
        }

        maya_file = glob.glob(version_dir + '/*.ma')[0].replace('\\', '/')
        high_usd = v_dir_usd + '/high.usd'
        uv_usd = v_dir_usd + '/uv.usd'
        batch_export_tex_usd(maya_file, high_usd, uv_usd, **args)
        Usd.Stage.Open(high_usd)
        Usd.Stage.Open(uv_usd)
        step_pub_usds.TexStepUsd(version_folder=version_dir,task_id=task_id,version_type=publish_type)

    except Exception:
        return traceback.format_exc()
