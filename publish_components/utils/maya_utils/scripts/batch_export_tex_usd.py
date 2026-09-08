import os
import json
import sys
import pymel.core as pm
import maya.cmds as cmds
import maya.standalone

def export(m_file, high_path, uv_path, **ars):
    maya.standalone.initialize()
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

    default_attrs.update({"file": uv_path, **ars})

    pm.loadPlugin('mayaUsdPlugin', quiet=True)
    pm.loadPlugin('mtoa', quiet=True)
    cmds.file(m_file, o=True, f=True)

    if cmds.getAttr("defaultRenderGlobals.outFormatControl") != 0:
        cmds.setAttr("defaultRenderGlobals.outFormatControl", 0)

    if not os.path.isdir(os.path.dirname(high_path)):
        os.makedirs(os.path.dirname(high_path))

    if os.path.isfile(high_path):
        os.remove(high_path)

    if os.path.isfile(uv_path):
        os.remove(uv_path)

    print("-"*10)
    print("export high usd attrs: \n{}".format(default_attrs))
    print("-"*10)
    pm.mayaUSDExport(**default_attrs)

    root_node = default_attrs.get("exportRoots", "|Root_grp|Geo_grp")
    cmds.select(root_node)
    cmds.arnoldExportAss(f=high_path, mask=14584, lightLinks=0, shadowLinks=0,
                         fullPath=1, exportAllShadingGroups=1, writeDefaults=True)
    maya.standalone.uninitialize()

if __name__ == "__main__":
    args = sys.argv[1:]
    maya_file = args[0]
    high_p = args[1]
    uv_p = args[2]
    arg_json = args[3]
    with open(arg_json, "r") as f:
        usd_args = json.load(f)
    export(maya_file, high_p, uv_p, **usd_args)