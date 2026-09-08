# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.utils as utils
from publish_components.utils.maya_utils import get_upstream_nodes

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查 high 组有 UDIM 贴图的几何体是否在 map1 这个 UV Set 有 UV；确保 UV 都在正向象限且不超过 10"""
    try:
        def use_udim_tex(mesh):
            for se in pm.listConnections(mesh, d=True, s=False, type='shadingEngine'):
                for n_name in get_upstream_nodes.get_nodes(se):
                    n = pm.PyNode(n_name)
                    if n.nodeType() == 'file' and n.uvTilingMode.get() == 3:
                        return True
                    elif n.nodeType == 'aiImage' and '<udim>' in n.filename.get().lower():
                        return True
            return False

        def check():
            l_no_map1 = []
            l_no_uvs = []
            l_bad_uvs = []
            d_srf_shaders = process_data['d_srf_shaders']
            l_tex_meshes = []
            for se_name, se_info in d_srf_shaders.items():
                if se_info['tex'] == '':
                    continue
                l_tex_meshes.extend(se_info['geo'])

            n_high = process_data.get('high', '|Root_grp|Geo_grp|high')
            for n in pm.listRelatives(n_high, ad=True, type='mesh'):
                if not n.name() in l_tex_meshes:
                    continue
                uvset_list = pm.polyUVSet(n, allUVSets=True, q=True)
                uvset_list.reverse()
                if not 'map1' in uvset_list:
                    l_no_map1.append(n.name())
                    continue

                current_set = pm.polyUVSet(n, currentUVSet=True, q=True)[0]
                if current_set != 'map1':
                    pm.polyUVSet(n, currentUVSet=True, uvSet='map1')

                uv_bbx = pm.polyEvaluate(n, boundingBox2d=True)

                if uv_bbx[0][0] < 0.0 or uv_bbx[0][1] > 10.0 or uv_bbx[1][0] < 0.0 or uv_bbx[1][1] > 10.0:
                    if not use_udim_tex(n):
                        continue
                    else:
                        l_bad_uvs.append(n.name())

            return l_no_map1, l_no_uvs, l_bad_uvs

        no_map1, no_uvs, bad_uvs = utils.executeInMainThreadWithResult(check)
        err_msgs = []
        if no_map1:
            err_msgs.append(u'有贴图但没有 map1 这个 uvset 的几何体：\n' + u'\n'.join(no_map1))
        if no_uvs:
            err_msgs.append(u'有贴图但没 UV 的几何体：\n' + u'\n'.join(no_uvs))
        if bad_uvs:
            err_msgs.append(u"uv超出 0-10 象限的面: \n" + u'\n'.join(bad_uvs))

        if err_msgs:
            return '\n'.join(err_msgs)

    except Exception:
        return traceback.format_exc()

