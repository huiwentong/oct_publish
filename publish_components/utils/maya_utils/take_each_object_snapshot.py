# -*- coding: utf-8 -*-

import os

import pymel.core as pm
import maya.cmds as cmds
import maya.mel as mel


def main(group_list, output_dir, start_frame=1, only_set=False):
    """
    为每个物体组创建缩略图。

    该方法的执行步骤
    1.创建一个用于拍屏的摄像机
    2.将playblast视窗设置为该相机视图
    3.遍历物体组，在相机视图下居中每个资产组(快捷键f操作)，摄像机逐帧key帧
    4.隐藏所有的物体, 并设置关键帧，每个物体组仅显示一帧
    5.执行拍屏
    6.按照资产名称修改拍屏文件名
    7.删除摄像机
    8.还原物体的显示属性

    Args:
        group_list: list, 由longname(str)组成的列表
        output_dir: str, 输出目录
        start_frame: int, 开始帧
        only_set: bool, 仅设置关键帧，不执行拍屏

    Returns:
        None
    """

    # 创建一个snap相机，将playblast视窗设置为该相机视图
    snap_camera, _ = cmds.camera(name='snapshot_cam')
    cmds.setAttr(snap_camera + '.nearClipPlane', 0.5)
    cmds.setAttr(snap_camera + '.farClipPlane', 100000000)
    mel.eval('setNamedPanelLayout("Single Perspective View")')
    active_panel_name = cmds.playblast(activeEditor=True)
    active_panel_name = active_panel_name.split('|')[-1]
    cmds.modelPanel(active_panel_name, e=True, camera=snap_camera)

    # 当前视窗设置
    cmds.modelEditor(active_panel_name, e=True, useDefaultMaterial=False)
    cmds.modelEditor(active_panel_name, e=True, displayAppearance='smoothShaded')
    cmds.modelEditor(active_panel_name, e=True, wireframeOnShaded=False)
    cmds.modelEditor(active_panel_name, e=True, displayTextures=True)
    cmds.modelEditor(active_panel_name, e=True, shadingModel=True)
    cmds.modelEditor(active_panel_name, e=True, polymeshes=True)
    cmds.modelEditor(active_panel_name, e=True, twoSidedLighting=True)
    cmds.modelEditor(active_panel_name, e=True, displayLights='default')


    # 为摄像机key帧
    current_frame = start_frame
    for grp in group_list:
        cmds.currentTime(current_frame, e=True)
        cmds.select(grp, replace=True)
        cmds.viewFit(snap_camera)
        cmds.setKeyframe(snap_camera, time=current_frame)
        current_frame += 1

    # 隐藏所有的物体, 并设置关键帧
    end_frame = start_frame + len(group_list) - 1
    all_mesh = [i.getParent() for i in pm.ls(type='mesh')]
    for mesh in all_mesh:
        for num in range(start_frame, end_frame+1):
            pm.setKeyframe(mesh.attr('visibility'), time=num, value=0)

    # 对每个物体组的显示属性设置关键帧，每一帧仅显示一个物体组
    current_frame = start_frame
    for grp in group_list:
        mesh_list = pm.listRelatives(pm.PyNode(grp), children=True, allDescendents=True, type='mesh')
        for mesh in mesh_list:
            transform_node = mesh.getParent()
            pm.setKeyframe(transform_node.attr('visibility'), time=current_frame, value=1)
        current_frame += 1
    
    if only_set:
        return

    # 开始拍屏
    print('output_dir: {0}'.format(output_dir))
    cmds.select(clear=True)
    default_render_edit = pm.PyNode('defaultResolution')
    width = default_render_edit.width.get()
    height = default_render_edit.height.get()

    cmds.playblast(
        format='image',
        filename=os.path.join(output_dir, 'snapshot'),
        sequenceTime=0,
        clearCache=1,
        viewer=0,
        showOrnaments=False,
        fp=1,
        percent=100,
        compression='png',
        quality=100,
        widthHeight=(width, height),
        startTime=start_frame,
        endTime=end_frame
        )

    # 按照资产名称修改拍屏文件名
    current_frame = start_frame
    for grp in group_list:
        s_file = os.path.join(output_dir, 'snapshot.{0}.png'.format(current_frame))
        t_file = os.path.join(output_dir, '{0}.png'.format(grp.split('|')[-1]))
        if os.path.exists(s_file) and not os.path.exists(t_file):
            os.rename(s_file, t_file)
            print('{0} -> {1}'.format(grp, t_file))
        else:
            if not os.path.exists(s_file):
                print('{0} not found'.format(s_file))
            if os.path.exists(t_file):
                print('{0} already exists'.format(t_file))
            
        current_frame += 1

    # 删除摄像机
    if cmds.objExists(snap_camera):
        cmds.delete(snap_camera)
    
    # 还原物体的显示属性
    for mesh in all_mesh:
        pm.cutKey(mesh.attr('visibility'))
        mesh.attr('visibility').set(1)
