# -*- coding: utf-8 -*-
import traceback

import maya.cmds as cmds
import maya.utils as utils

# mayaUSD 能转成 UsdPreviewSurface 的材质球，以及材质网络里允许出现的贴图 / 工具节点
SHADER_TYPES = {'lambert', 'blinn', 'phong', 'standardSurface', 'usdPreviewSurface'}
TEXTURE_TYPES = {'file', 'place2dTexture'}
# 只看渲染节点；groupId、defaultColorMgtGlobals 这类连在材质网络上的非渲染节点没有这些分类。
# Arnold 节点都带 rendernode/arnold
RENDER_CLASSIFICATIONS = ('shader/', 'texture/', 'utility/', 'rendernode/')


def find_errors():
    """返回 (|lay|efx_grp 下的 reference 节点, 不在白名单里的材质网络节点)。需在 Maya 主线程调用。"""
    ref_nodes, bad_shading = [], []
    if cmds.objExists('|lay|efx_grp'):
        nodes = cmds.listRelatives('|lay|efx_grp', allDescendents=True, fullPath=True) or []
        ref_nodes = [n for n in nodes if cmds.referenceQuery(n, isNodeReferenced=True)]

        meshes = cmds.ls(nodes, type='mesh', noIntermediate=True, long=True)
        shading_engines = set(cmds.listConnections(meshes, type='shadingEngine') or []) if meshes else set()
        for sg in sorted(shading_engines):
            # pruneDagObjects：只往材质网络上游找，不顺着 SG 成员走到 mesh
            for node in cmds.listHistory(sg, pruneDagObjects=True) or []:
                node_type = cmds.nodeType(node)
                classification = ' '.join(cmds.getClassification(node_type))
                # 没加载 mtoa 时 Arnold 节点会变成 unknown，同样不允许
                is_render_node = node_type == 'unknown' or any(c in classification for c in RENDER_CLASSIFICATIONS)
                if is_render_node and node_type not in SHADER_TYPES | TEXTURE_TYPES:
                    bad_shading.append((sg, node, node_type))
    return ref_nodes, bad_shading


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    检查 |lay|efx_grp 特效示意：不允许 reference，材质只允许 Maya 自带材质 + file 贴图
    """
    # 示意会由 export_shot_usd 导成 USD 给 fx 参考：
    #   reference 进来的资产会被角色缓存和示意各导一次，贴图也不会被拷进版本目录；
    #   农场导出环境不带 mtoa，白名单外的材质节点不会转成 UsdPreviewSurface，贴图会丢。
    # 不提供 fix。
    try:
        def check():
            ref_nodes, bad_shading = find_errors()
            error_nodes = ref_nodes + [node for _, node, _ in bad_shading]
            if error_nodes:
                cmds.select(error_nodes)
            return ref_nodes, bad_shading

        ref_nodes, bad_shading = utils.executeInMainThreadWithResult(check)
        msg = ''
        if ref_nodes:
            msg += u"|lay|efx_grp 下不允许有 reference，请 Import Reference 或移出 efx_grp：\n" + '\n'.join(ref_nodes) + '\n'
        if bad_shading:
            msg += u"|lay|efx_grp 下的材质只允许 {0} + {1}，以下节点不允许：\n".format(
                ' / '.join(sorted(SHADER_TYPES)), ' / '.join(sorted(TEXTURE_TYPES)))
            msg += '\n'.join(u'{0}: {1} ({2})'.format(*item) for item in bad_shading)
        if msg:
            return msg
    except:
        return traceback.format_exc()
