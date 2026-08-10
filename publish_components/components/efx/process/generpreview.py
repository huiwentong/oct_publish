
import os
import sys
import argparse
import maya.standalone
import maya.cmds as cmds
import maya.api.OpenMaya as om
import maya.mel as mel

import hashlib
from xml.dom.minidom import Document


def get_custom_root_nodes():
    all_roots = cmds.ls(assemblies=True)
    default_nodes = ["persp", "top", "front", "side"]
    custom_roots = [node for node in all_roots if node not in default_nodes]

    return custom_roots


def reset_scale_to_one(node_name):
    axes = ['X', 'Y', 'Z']
    for axis in axes:
        attr = f"{node_name}.scale{axis}"
        current_scale = cmds.getAttr(attr)
        if abs(current_scale - 1.0) > 0.0001:
            print(f"修正 {attr}: {current_scale} -> 1.0")
            cmds.setAttr(attr, 1.0)


def create_structure(root_elem, root_node, doc):
    if not cmds.objExists(root_node):
        return
    l_nodes = cmds.listRelatives(root_node, fullPath=True) or []

    for node in l_nodes:
        node_type = cmds.nodeType(node)

        if node_type == 'transform':
            trans = doc.createElement('transform')
            trans.setAttribute('name', node)
            root_elem.appendChild(trans)
            create_structure(trans, node, doc)

        elif node_type == 'mesh' and (not cmds.getAttr(node + ".intermediateObject")):
            face_count = cmds.polyEvaluate(node, face=True)

            if face_count == 0:
                topology = hashlib.md5(b' ').hexdigest()
            else:
                sl = om.MSelectionList()
                sl.add(node)
                mesh_dag = sl.getDagPath(0)
                mesh_mfn = om.MFnMesh(mesh_dag)

                v = mesh_mfn.getVertices()
                v_str0 = '[' + ', '.join([str(i) for i in v[0]]) + ']'
                v_str1 = '[' + ', '.join([str(i) for i in v[1]]) + ']'
                v_str = v_str0 + ' ' + v_str1

                try:
                    topology = hashlib.md5(v_str).hexdigest()
                except TypeError:
                    topology = hashlib.md5(v_str.encode('utf-8')).hexdigest()

            mesh = doc.createElement('mesh')
            mesh.setAttribute('name', node)
            mesh.setAttribute('vertex', str(cmds.polyEvaluate(node, vertex=True)))
            mesh.setAttribute('edge', str(cmds.polyEvaluate(node, edge=True)))
            mesh.setAttribute('face', str(face_count))
            mesh.setAttribute('topology', topology)
            root_elem.appendChild(mesh)

    return


def export_xml(xml_file):
    n_root = '|Root_grp'
    n_geo = '|Root_grp|Geo_grp'
    n_high = '|Root_grp|Geo_grp|high'

    doc = Document()
    master = doc.createElement('transform')
    master.setAttribute('name', n_root)
    doc.appendChild(master)
    poly = doc.createElement('transform')
    poly.setAttribute('name', n_geo)
    master.appendChild(poly)

    if cmds.objExists(n_high):
        res_node = doc.createElement('transform')
        res_node.setAttribute('name', n_high)
        poly.appendChild(res_node)
        create_structure(res_node, n_high, doc)

    f = open(xml_file, 'w')
    f.write(doc.toprettyxml(indent='    '))
    f.close()



def export_usd(usd_dir):
    if not os.path.isdir(usd_dir):
        os.makedirs(usd_dir)
    usd_path = usd_dir + '/high.usd'
    if os.path.isfile(usd_path):
        os.remove(usd_path)

    n_geogrp_name = '|Root_grp|Geo_grp'
    cmds.mayaUSDExport(
        file=usd_path,
        exportRoots=[n_geogrp_name],  # 必须是列表格式
        exportUVs=True,
        exportSkels='none',
        exportSkin='none',
        exportBlendShapes=False,
        exportColorSets=True,
        defaultMeshScheme='none',
        defaultUSDFormat='usdc',
        eulerFilter=False,
        staticSingleSample=False,
        frameStride=1.0,  # cmds 中部分版本要求浮点数
        frameSample=0.0,
        parentScope='',
        exportDisplayColor=False,
        shadingMode='useRegistry',
        convertMaterialsTo=['UsdPreviewSurface'],  # 部分版本此处需用列表
        exportInstances=True,
        exportVisibility=True,
        mergeTransformAndShape=False,
        stripNamespaces=True
    )



def main(scene_path=None, render_folder=None, cache_file=None):
    maya.standalone.initialize()
    # scene_path = "C:/path/to/your/scene.mb"
    # render_folder = "C:/temp/my_render"
    print(render_folder)
    ver_folder = os.path.dirname(scene_path)
    plugin_name = "mayaUsdPlugin"

    if not cmds.pluginInfo(plugin_name, query=True, loaded=True):
        try:
            cmds.loadPlugin(plugin_name)
            print(f"成功加载插件: {plugin_name}")
        except:
            print(f"无法加载插件: {plugin_name}，请检查是否已安装 USD 扩展。")
    else:
        print(f"插件 {plugin_name} 已经处于加载状态。")
    # cmds.file(scene_path, open=True, force=True)
    cmds.file(rename=scene_path)
    mel.eval(f'file -import -type "USD Import"  -ignoreVersion -ra true -mergeNamespacesOnClash true -namespace ":" "{cache_file}";')



    target_object = get_custom_root_nodes()[0]
    reset_scale_to_one(target_object)

    if cmds.objExists(target_object):
        cmds.select(target_object)
    else:
        print(f"Error: 找不到对象 {target_object}")
        return

    new_geo_name = cmds.rename(target_object, "Geo_grp")
    root_grp = cmds.group(em=True, name="Root_grp")
    cmds.parent(new_geo_name, root_grp)



    cmds.setAttr("defaultRenderGlobals.imageFilePrefix", os.path.splitext(render_folder)[0], type="string")
    cmds.viewFit('persp', fitFactor=0.9)
    cmds.setAttr("defaultRenderGlobals.currentRenderer", "mayaSoftware", type="string")
    cmds.setAttr("defaultRenderGlobals.imageFormat", 32) 
    cmds.file(save=True, force=True, type="mayaAscii")
    cmds.render('persp', batch=False)
    print("渲染完成！")
    export_usd(ver_folder + '/usd')
    export_xml(ver_folder + '/mesh.xml')
    maya.standalone.uninitialize()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Render a Maya scene.")
    parser.add_argument("--scene", help="Path to the Maya scene file")
    parser.add_argument("--render_folder", help="Path to the render output folder")
    parser.add_argument("--cache", help="Path to usd cache")
    args = parser.parse_args()
    main(scene_path=args.scene, render_folder=args.render_folder, cache_file=args.cache)