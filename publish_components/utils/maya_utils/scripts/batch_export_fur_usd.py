import os
import sys
import traceback
import pymel.core as pm
import maya.cmds as cmds
import maya.standalone

def create_cubes_for_all_materials():
    materials = cmds.ls(materials=True)
    for i, mat in enumerate(materials):
        try:
            cube = cmds.polyCube(name=f"{mat}_cube")[0]
            cmds.move(i * 3, 0, 0, cube)
            sg_nodes = cmds.listConnections(mat, type="shadingEngine")
            if not sg_nodes:
                sg_nodes = [cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=f"{mat}SG")]
                cmds.connectAttr(f"{mat}.outColor", f"{sg_nodes[0]}.surfaceShader", force=True)
            cmds.sets(cube, e=True, forceElement=sg_nodes[0])
        except Exception as e:
            traceback.print_exc()
            continue
    print(f"has handle {{len(materials)}} mats")

def export(m_file, high_path, **ars):
    maya.standalone.initialize()

    pm.loadPlugin('mayaUsdPlugin', quiet=True)
    pm.loadPlugin('mtoa', quiet=True)
    cmds.file(m_file, o=True, f=True)

    if cmds.getAttr("defaultRenderGlobals.outFormatControl") != 0:
        cmds.setAttr("defaultRenderGlobals.outFormatControl", 0)

    if not os.path.isdir(os.path.dirname(high_path)):
        os.makedirs(os.path.dirname(high_path))

    if os.path.isfile(high_path):
        os.remove(high_path)

    create_cubes_for_all_materials()
    cmds.select(all=True)
    cmds.arnoldExportAss(f=high_path, mask=14584, lightLinks=0, shadowLinks=0,
                         fullPath=1, exportAllShadingGroups=1, writeDefaults=True)
    maya.standalone.uninitialize()

if __name__ == "__main__":
    args = sys.argv[1:]
    maya_file = args[0]
    high_p = args[1]
    export(maya_file, high_p)