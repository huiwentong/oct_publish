# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.utils as utils
from importlib import reload
from publish_components.utils.maya_utils import get_upstream_nodes
reload(get_upstream_nodes)


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查 map1 是不是空 UV Set,如果没有贴图，自动给一个 UV; 有贴图的 mesh, 需要手动展 UV"""

    try:
        def get_tex_meshes():
            d_srf_shaders = process_data.get('d_srf_shaders', {})
            tex_meshes = []

            for se_name, se_info in d_srf_shaders.items():
                l_nodes = []
                get_upstream_nodes.iter_upstream(se_name, l_nodes)

                has_texture = False
                for node_name in l_nodes:
                    if pm.nodeType(node_name) in ['file', 'aiImage']:
                        has_texture = True
                        break

                if has_texture:
                    tex_meshes.extend(se_info['geo'])

            return tex_meshes

        def delete_history(_meshes):
            transforms = []

            for m in _meshes:
                if 'proxyShape' in m.name():
                    continue

                transform = m.getParent()
                if transform not in transforms:
                    transforms.append(transform)

            if transforms:
                pm.delete(transforms, ch=True)

            pm.select(clear=True)

        l_mesh_need_uv = []
        l_tex_meshes = get_tex_meshes()
        n_high = process_data.get('high', '|Root_grp|Geo_grp|high')

        meshes = pm.listRelatives(n_high, ad=True, type='mesh')

        for mesh in meshes:
            if 'proxyShape' in mesh.name():
                continue

            pm.polyUVSet(mesh, uvSet='map1', currentUVSet=True)
            uv_cnt = pm.polyEvaluate(mesh, uvcoord=True)

            if uv_cnt == 0:
                if mesh.name() in l_tex_meshes:
                    l_mesh_need_uv.append(mesh.name())
                else:
                    pm.polyAutoProjection(mesh)

        utils.executeInMainThreadWithResult(lambda :delete_history(meshes))
        if l_mesh_need_uv:
            return u"以下面，带贴图却没有展 UV，请手动展UV:\n  " + ' '.join(l_mesh_need_uv)

    except Exception:
        return traceback.format_exc()
