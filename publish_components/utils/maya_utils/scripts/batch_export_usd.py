import os
import json
import sys
import pymel.core as pm
import maya.cmds as cmds

def export(m_file, out_path, **ars):

    default_attrs = {
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

    default_attrs.update({"file": out_path, **ars})

    pm.loadPlugin('mayaUsdPlugin', quiet=True)
    pm.loadPlugin('mtoa', quiet=True)
    cmds.file(m_file, o=True, f=True)
    if not os.path.isdir(os.path.dirname(out_path)):
        os.makedirs(os.path.dirname(out_path))

    if os.path.isfile(out_path):
        os.remove(out_path)
    print("-"*10)
    print("export usd attrs: \n{}".format(default_attrs))
    print("-"*10)
    pm.mayaUSDExport(**default_attrs)

if __name__ == "__main__":
    args = sys.argv[1:]
    maya_file = args[0]
    out_usd_path = args[1]
    arg_json = args[2]
    with open(arg_json, "r") as f:
        usd_args = json.load(f)
    export(maya_file, out_usd_path, **usd_args)