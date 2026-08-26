# -*- coding:utf-8 -*-

import traceback
import os
import sys
import shutil
import math
import importlib
from xml.etree import ElementTree


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
导出 Scene Graph XML
    """

    def create_flg_low(self, n_geo, abc_path):
        if not pm.objExists(n_geo.fullPath() + '|high'):
            return
        if pm.objExists(n_geo.fullPath() + '|low'):
            return

        n_high = pm.PyNode(n_geo.fullPath() + '|high')
        n_low = pm.duplicate(n_high, name='low')[0]

        l_leaf_nodes = []
        l_twig_nodes = []
        for n in pm.listRelatives(n_low, ad=True, type='mesh'):
            if pm.polyEvaluate(n, f=True) < 1000:
                continue
            tokens = n.fullPath().lower().split('|')
            is_leaf = False
            is_twig = False

            for t in tokens:
                if 'leaf' in t or 'leaves' in t:
                    is_leaf = True

            if is_leaf:
                l_leaf_nodes.append(n.name())
            else:
                for t in tokens:
                    if 'twig' in t:
                        is_twig = True
                if is_twig:
                    l_twig_nodes.append(n.name())

        from tk_oct_publish.proc import export_proxy_cache as epc
        try:
            importlib.reload(epc)
        except AttributeError:
            reload(epc)

        for n in pm.listRelatives(n_low, ad=True, type='mesh'):
            n_p = n.getParent()
            if n.name() in l_leaf_nodes:
                bbx = n_p.boundingBox()
                center = ((bbx[0][0] + bbx[1][0])/2, (bbx[0][1] + bbx[1][1])/2, (bbx[0][2] + bbx[1][2])/2)
                radius = math.sqrt((bbx[0][0] - bbx[1][0])**2 + (bbx[0][1] - bbx[1][1])**2 + (bbx[0][2] - bbx[1][2])**2) / 2.0
                n_t, n_sphere = pm.polySphere()
                n_sphere.radius.set(radius)
                n_t.tx.set(center[0])
                n_t.ty.set(center[1])
                n_t.tz.set(center[2])
                n_t.rename(n_p.nodeName() + '_wrap')
                n_t.setParent(n_p.getParent())

                pm.select(n_t)
                sw = pm.deformer(type="shrinkWrap")[0]
                pm.connectAttr(n.fullPath() + ".worldMesh[0]", sw.name() + ".targetGeom", f=True)
                sw.projection.set(4)
                pm.select(n_t, r=True)
                pm.mel.eval('DeleteHistory;')
                pm.delete(n_p)
            elif n.name() in l_twig_nodes:
                pm.delete(n_p)
            else:
                epc.poly_reduce(n, 75)

        pm.AbcExport(j=" -writeColorSets -frameRange 1 1 -uvWrite -root " + n_low.fullPath() + " -file " + abc_path)
        pm.delete(n_low)
        return

    def proceed():
        print(self.dialog.d_assets_info)
        if self.dialog.entity['sg_asset_type'].lower() == "scn":
            return ""

        import pymel.core as pm
        global pm
        from tk_oct_publish.proc.sceneGraphXML import maya2scenegraphXML
        try:
            importlib.reload(maya2scenegraphXML)
        except AttributeError:
            reload(maya2scenegraphXML)
        pm.loadPlugin('AbcExport', quiet=True)
        pm.loadPlugin('AbcImport', quiet=True)

        proc_path = __file__.split('publish_process')[0].replace('\\', '/') + '/proc/sceneGraphXML'
        pm.mel.eval('python(\"import sys;sys.path.append(\\\"{}\\\");import maya2scenegraphXML\");'.format(proc_path))

        try:
            for asset_name, asset_info in self.dialog.d_assets_info.items():
                n_root = asset_info['root']
                n_geo = asset_info['geo']
                n_high = asset_info['high']
                n_parent = n_root.getParent()
                n_root.setParent(None)

                v_dir_tmp = asset_info['v_dir_tmp']
                asset_type = asset_info['sg_asset_type']

                if os.path.isdir(v_dir_tmp + '/scene_graph_xml'):
                    shutil.rmtree(v_dir_tmp + '/scene_graph_xml')

                os.makedirs(v_dir_tmp + '/scene_graph_xml')

                xmlFilePath = v_dir_tmp + '/scene_graph_xml/' + asset_name + '.xml'

                maya2scenegraphXML.deleteSgxmlAttrs(n_root.fullPath())
                for t in pm.listRelatives(n_root, c=True):
                    if t.nodeName() not in ['Geometry', 'Geo_grp']:
                        maya2scenegraphXML.setIgnore([t.fullPath()])

                res_list = []
                for t in pm.listRelatives(n_geo, c=True):
                    res = t.nodeName().split(':')[-1]
                    res_list.append(res)
                    if res not in ['high', 'temp']:
                        maya2scenegraphXML.setIgnore([t.fullPath()])
                        if res == 'low':
                            abc_path = v_dir_tmp + '/scene_graph_xml/' + res + '.abc'
                            pm.AbcExport(
                                j=" -writeColorSets -frameRange 1 1 -uvWrite -root " + t.fullPath() + " -file " + abc_path)
                    else:
                        maya2scenegraphXML.setComponent([t.fullPath()], refType='abc')
                        t.visibility.set(True)

                task_step = self.dialog.step['short_name']
                if task_step not in ['tex']:
                    maya2scenegraphXML.setProxy([n_root.fullPath()], 'proxy.abc')

                # maya2scenegraphXML.maya2ScenegraphXML([n_root.fullPath()], xmlFilePath, startFrame=1, endFrame=1, arbAttrs=[])
                pm.mel.eval(
                    'python(\"maya2scenegraphXML.maya2ScenegraphXML([\\\"{}\\\"], \\\"{}\\\", startFrame=1, endFrame=1, arbAttrs=[])\")'.format(
                        n_root.fullPath(), xmlFilePath))

                if task_step not in ['tex']:
                    f_low_abc = v_dir_tmp + '/scene_graph_xml/low.abc'
                    f_high_abc = v_dir_tmp + '/scene_graph_xml/high.abc'

                    if asset_type == 'FLG':
                        self.create_flg_low(n_geo, f_low_abc)

                    # export proxy at here, since high.abc exported after the line above
                    from tk_oct_publish.proc import export_proxy as export_proxy
                    try:
                        importlib.reload(export_proxy)
                    except AttributeError:
                        reload(export_proxy)

                    if os.path.isfile(f_low_abc):
                        self.dialog.print_log('proxy_source_path: ' + f_low_abc)
                        proxy_ret = export_proxy.export_proxy_cache(f_low_abc, percentage=50)
                    elif os.path.isfile(f_high_abc):
                        self.dialog.print_log('proxy_source_path: ' + f_high_abc)
                        proxy_ret = export_proxy.export_proxy_cache(f_high_abc, percentage=85)
                    else:
                        proxy_ret = 'Neither low.abc nor high.abc exists. Skip exporting proxy.abc'

                    if proxy_ret:
                        self.dialog.print_log(proxy_ret)

                maya2scenegraphXML.deleteSgxmlAttrs(n_root.fullPath())

                pm.select(cl=True)
                n_root.setParent(n_parent)

            return ""

        except:
            return traceback.format_exc()

    proceed()