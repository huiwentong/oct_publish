# -*- coding: utf-8 -*-
import traceback, os
import pymel.core as pm
import maya.utils as utils
from contextlib import contextmanager


@contextmanager
def exclude_clay_shaders():
    """Export the default layer while omitting temporary clay networks."""
    import maya.cmds as cmds
    import maya.OpenMaya as om
    import maya.app.renderSetup.model.renderSetup as renderSetup

    excluded_names = {
        'clay_grey_aiStandardSurface',
        'clay_grey_aiStandardSurface_displacement',
        'clay_grey_aiStandardSurface_displacement_displacement',
    }
    setup = renderSetup.instance()
    original_layer = setup.getVisibleRenderLayer()
    write_states = []
    try:
        setup.switchToLayer(setup.getDefaultRenderLayer())
        excluded_nodes = set(
            node for node in cmds.ls(dependencyNodes=True)
            if node.rsplit(':', 1)[-1] in excluded_names
        )
        shading_groups = set()
        for node in excluded_nodes:
            shading_groups.update(cmds.listConnections(
                node, source=False, destination=True, type='shadingEngine'
            ) or [])
        excluded_nodes.update(shading_groups)
        for node in excluded_nodes:
            selection = om.MSelectionList()
            selection.add(node)
            obj = om.MObject()
            selection.getDependNode(0, obj)
            fn = om.MFnDependencyNode(obj)
            write_states.append((fn, not fn.canBeWritten()))
            fn.setDoNotWrite(True)
        yield excluded_nodes
    finally:
        try:
            for fn, do_not_write in reversed(write_states):
                fn.setDoNotWrite(do_not_write)
        finally:
            setup.switchToLayer(original_layer)


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """将贴图路径指向服务器后导出资产文件"""
    try:
        def get_imgs_info():
            imgs_info = {'file': {}, 'aiImage': {}}
            for n in pm.ls(type='file'):
                imgs_info['file'][n.nodeName()] = n.getAttr('fileTextureName')
            for n in pm.ls(type='aiImage'):
                imgs_info['aiImage'][n.nodeName()] = n.getAttr('filename')
            return imgs_info

        def reset_imgs(imgs_d):
            for n in pm.ls(type='file'):
                cs = n.getAttr('colorSpace')
                n.setAttr('fileTextureName', imgs_d['file'][n.nodeName()])
                n.setAttr('colorSpace', cs, type='string')
            for n in pm.ls(type='aiImage'):
                cs = n.getAttr('colorSpace')
                n.setAttr('filename', imgs_d['aiImage'][n.nodeName()])
                n.setAttr('colorSpace', cs, type='string')

        def process():
            d_imgs = get_imgs_info()
            v_dir_imgs = process_data['v_dir_imgs']
            v_dir_ma_file = process_data['v_dir_ma_file']
            n_root = pm.PyNode(process_data.get('root', '|Root_grp'))
            try:
                for n in pm.ls(type='file'):
                    cs = n.getAttr('colorSpace')
                    n.setAttr('fileTextureName', v_dir_imgs + '/' + os.path.basename(d_imgs['file'][n.nodeName()]))
                    n.setAttr('colorSpace', cs, type='string')
                for n in pm.ls(type='aiImage'):
                    cs = n.getAttr('colorSpace')
                    n.setAttr('filename', v_dir_imgs + '/' + os.path.basename(d_imgs['aiImage'][n.nodeName()]))
                    n.setAttr('colorSpace', cs, type='string')

                pm.select(n_root, r=True)
                if pm.objExists('Sets'):
                    pm.select('Sets', add=True, ne=True)

                # export script node
                for node in pm.ls(type="script"):
                    if node.name() in ["sceneConfigurationScriptNode"]:  # default node
                        continue
                    if pm.objExists("{}.a".format(node.name())) or pm.objExists("{}.b".format(node.name())):
                        pm.select(node, add=True, ne=True)

                # unexport reference nodes
                export_nodes = [node for node in pm.selected()
                                if not pm.referenceQuery(node, isNodeReferenced=True)]

                with exclude_clay_shaders() as excluded_nodes:
                    pm.select([node for node in export_nodes if node.name() not in excluded_nodes],
                              r=True, ne=True)
                    pm.exportSelected(v_dir_ma_file, force=True, options="v=0;",
                                      type="mayaAscii", pr=True, es=True)
                pm.select(cl=True)
            finally:
                reset_imgs(d_imgs)

        utils.executeInMainThreadWithResult(process)


    except Exception:
        return traceback.format_exc()
