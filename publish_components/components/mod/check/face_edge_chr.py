# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.cmds as cmds
import maya.utils as utils
import maya.api.OpenMaya as om
from publish_components.utils.sg_helper import get_asset_kind, UE_SCENE_TAG

def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
    检查不能大于四边面
    """
    try:
        def check():
            d_invalid = {}
            l_invalid_faces = []
            n_geo = process_data.get('geo', '|Root_grp|Geo_grp')
            n_geo = pm.PyNode(n_geo)

            l_meshes = pm.listRelatives(n_geo, ad=True, type='mesh', path=True) or []
            for mesh_node in l_meshes:
                sl = om.MSelectionList()
                sl.add(mesh_node.fullPath())
                mesh_dag = sl.getDagPath(0)
                mesh_mfn = om.MFnMesh(mesh_dag)

                for i in range(mesh_mfn.numPolygons):
                    if mesh_mfn.polygonVertexCount(i) > 4:
                        d_invalid.setdefault(str(mesh_node), []).append(i)
                        l_invalid_faces.append(str(mesh_node + '.f[' + str(i) + ']'))

            if len(d_invalid) > 0:
                pm.select(l_invalid_faces, r=True)
            return d_invalid, l_invalid_faces

        process_data['face_edge_chr_error_faces'] = []
        # UE 场景资产不做这项检查
        if get_asset_kind(process_data.get('task_id')) != UE_SCENE_TAG:
            invalid_data, invalid_faces = utils.executeInMainThreadWithResult(check)
            if len(invalid_data) > 0:
                process_data['face_edge_chr_error_faces'] = invalid_faces
                # 每个模型附一条可直接粘到 Script Editor 的选择命令；面只列前 20 个，多了会刷屏
                return u'有些polygon几何体有多于4条棱的面（点击 fix 打开面列表逐个定位）:\n' + '\n'.join(
                    u'{}: {} 个面{}\ncmds.select({}, r=True)'.format(
                        mesh, len(ids), u'（只列前 20 个）' if len(ids) > 20 else '',
                        ['{}.f[{}]'.format(mesh, i) for i in ids[:20]])
                    for mesh, ids in invalid_data.items())

    except:
        return traceback.format_exc()


def fix(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
    打开面列表，点击列表项选中对应的面，方便逐个排查，不自动修复
    """
    try:
        def _show():
            faces = process_data.get('face_edge_chr_error_faces', [])
            win = 'face_edge_chr_faces_win'
            if cmds.window(win, exists=True):
                cmds.deleteUI(win)

            def on_select(*args):
                selected = cmds.textScrollList(face_list, q=True, selectItem=True) or []
                # 美术改完模型面编号会变，已经不存在的面跳过
                existed = [f for f in selected if cmds.objExists(f)]
                if not existed:
                    return
                # 先 hilite 再选：hilite -r 会把不在高亮列表里的物体的已选组件取消掉，
                # 而且要 hilite transform，面是挂在 transform 下的（DunJi.f[...]），hilite shape 会把它们取消
                transforms = cmds.listRelatives(cmds.ls(existed, objectsOnly=True), parent=True, fullPath=True)
                cmds.hilite(transforms, r=True)
                cmds.select(existed, r=True)

            cmds.window(win, title=u'多于四边的面（共 {} 个，点击选中，可多选）'.format(len(faces)),
                        widthHeight=(420, 500))
            cmds.columnLayout(adjustableColumn=True, rowSpacing=6)
            cmds.text(label=u'点击下方列表即可选中对应的面。\n本工具仅用于定位问题面，不会自动修复，请手动处理。',
                      align='left')
            face_list = cmds.textScrollList(append=faces, allowMultiSelection=True, height=440,
                                            selectCommand=on_select)
            cmds.showWindow(win)
            logger.warning(u"已打开面列表，共 {} 个多于四边的面，fix 不会自动修复，请手动处理".format(len(faces)))

        utils.executeInMainThreadWithResult(_show)

    except:
        return traceback.format_exc()