# -*- coding: utf-8 -*-

import os

import maya.cmds as cmds
import maya.mel as mel
import pymel.core as pm


def _set_attr(attr_name: str, value: object) -> None:
    """按 Maya 属性类型恢复属性值。

    Maya 的空字符串属性通过 ``getAttr`` 读取时可能返回 ``None``，因此不能
    仅根据 Python 值类型判断是否需要传入 ``type="string"``。

    Args:
        attr_name: Maya 属性的完整名称。
        value: 要恢复或写入的属性值。
    """
    attr_type = cmds.getAttr(attr_name, type=True)
    if attr_type == "string":
        cmds.setAttr(
            attr_name,
            "" if value is None else value,
            type="string",
        )
    else:
        cmds.setAttr(attr_name, value)


def _render_hardware_snapshot(
    camera: str,
    output_file: str,
    width: int,
    height: int,
) -> None:
    """使用 Maya Hardware 2.0 离屏渲染当前帧。

    Args:
        camera: 用于渲染的 Maya 相机节点。
        output_file: 目标 PNG 文件路径。
        width: 输出图片宽度。
        height: 输出图片高度。

    Raises:
        RuntimeError: OGS 渲染后没有生成预期文件时。
    """
    output_file = os.path.abspath(output_file)
    output_prefix = os.path.splitext(output_file)[0].replace("\\", "/")
    cmds.setAttr(
        "defaultRenderGlobals.imageFilePrefix",
        output_prefix,
        type="string",
    )

    expected_files = cmds.renderSettings(
        firstImageName=True,
        fullPath=True,
        camera=camera,
    ) or []
    cmds.ogsRender(
        camera=camera,
        currentFrame=True,
        width=width,
        height=height,
        noRenderView=True,
    )

    rendered_file = next(
        (path for path in [output_file] + expected_files if os.path.isfile(path)),
        None,
    )
    if rendered_file is None:
        raise RuntimeError(
            "Maya Hardware 2.0 未生成缩略图: {}".format(output_file)
        )

    if os.path.normcase(rendered_file) != os.path.normcase(output_file):
        os.replace(rendered_file, output_file)


def _create_snapshot_lights(camera: str) -> list[str]:
    """创建跟随截图相机的临时补光灯组。

    ``ogsRender`` 不会继承 modelEditor 的 ``displayLights="default"``，
    因此在没有可用场景灯光时需要显式补光，避免离屏缩略图发黑。

    Args:
        camera: 截图相机的 transform 节点。

    Returns:
        渲染结束后需要删除的灯光 transform 节点列表。
    """
    ambient_shape = cmds.ambientLight(
        name="snapshot_fill_light",
        intensity=0.8,
    )
    key_shape = cmds.directionalLight(
        name="snapshot_key_light",
        intensity=1.0,
    )
    ambient_transform = cmds.listRelatives(
        ambient_shape,
        parent=True,
        fullPath=True,
    )[0]
    key_transform = cmds.listRelatives(
        key_shape,
        parent=True,
        fullPath=True,
    )[0]

    ambient_transform = cmds.parent(
        ambient_transform,
        camera,
        relative=True,
    )[0]
    key_transform = cmds.parent(
        key_transform,
        camera,
        relative=True,
    )[0]
    cmds.setAttr(key_transform + ".rotateX", -30.0)
    cmds.setAttr(key_transform + ".rotateY", 35.0)
    return [ambient_transform, key_transform]


def _render_batch_snapshots(
    group_list: list[str],
    output_dir: str,
    camera: str,
    start_frame: int,
    width: int,
    height: int,
) -> None:
    """在 mayapy 模式下逐资产离屏渲染缩略图。

    渲染期间临时切换到 Maya Hardware 2.0 和 PNG，结束后恢复场景原有的
    Render Globals，避免影响后续发布步骤。

    Args:
        group_list: 需要生成缩略图的资产组长名称列表。
        output_dir: 缩略图输出目录。
        camera: 已经完成逐帧取景的相机节点。
        start_frame: 第一个资产对应的帧号。
        width: 输出图片宽度。
        height: 输出图片高度。
    """
    render_attrs = (
        "defaultRenderGlobals.currentRenderer",
        "defaultRenderGlobals.imageFormat",
        "defaultRenderGlobals.imageFilePrefix",
        "defaultRenderGlobals.animation",
        "defaultRenderGlobals.outFormatControl",
    )
    original_values = {
        attr_name: cmds.getAttr(attr_name) for attr_name in render_attrs
    }
    snapshot_lights = []

    try:
        cmds.setAttr(
            "defaultRenderGlobals.currentRenderer",
            "mayaHardware2",
            type="string",
        )
        cmds.setAttr("defaultRenderGlobals.imageFormat", 32)
        cmds.setAttr("defaultRenderGlobals.animation", False)
        cmds.setAttr("defaultRenderGlobals.outFormatControl", 0)
        snapshot_lights = _create_snapshot_lights(camera)

        for offset, group_name in enumerate(group_list):
            cmds.currentTime(start_frame + offset, edit=True)
            output_file = os.path.join(
                output_dir,
                "{}.png".format(group_name.split("|")[-1]),
            )
            _render_hardware_snapshot(
                camera=camera,
                output_file=output_file,
                width=width,
                height=height,
            )
    finally:
        if snapshot_lights:
            cmds.delete(snapshot_lights)
        for attr_name, value in original_values.items():
            _set_attr(attr_name, value)


def _playblast_snapshots(
    group_list: list[str],
    output_dir: str,
    start_frame: int,
    end_frame: int,
    width: int,
    height: int,
) -> None:
    """在前台 Maya 中拍屏并按资产名称整理缩略图。

    Args:
        group_list: 需要生成缩略图的资产组长名称列表。
        output_dir: 缩略图输出目录。
        start_frame: 拍屏开始帧。
        end_frame: 拍屏结束帧。
        width: 输出图片宽度。
        height: 输出图片高度。
    """
    cmds.playblast(
        format="image",
        filename=os.path.join(output_dir, "snapshot"),
        sequenceTime=0,
        clearCache=1,
        viewer=0,
        showOrnaments=False,
        fp=1,
        percent=100,
        compression="png",
        quality=100,
        widthHeight=(width, height),
        startTime=start_frame,
        endTime=end_frame,
    )

    for offset, group_name in enumerate(group_list):
        current_frame = start_frame + offset
        source_file = os.path.join(
            output_dir,
            "snapshot.{}.png".format(current_frame),
        )
        target_file = os.path.join(
            output_dir,
            "{}.png".format(group_name.split("|")[-1]),
        )
        if os.path.exists(source_file) and not os.path.exists(target_file):
            os.rename(source_file, target_file)
            print("{} -> {}".format(group_name, target_file))
        else:
            if not os.path.exists(source_file):
                print("{} not found".format(source_file))
            if os.path.exists(target_file):
                print("{} already exists".format(target_file))


def main(
    group_list: list[str],
    output_dir: str,
    start_frame: int = 1,
    only_set: bool = False,
) -> None:
    """为每个物体组创建缩略图。

    前台 Maya 沿用原来的 playblast；通过 mayapy/maya.standalone 运行时，
    改用 Maya Hardware 2.0 对每个资产对应的帧做一次离屏渲染。

    Args:
        group_list: 资产组长名称列表。
        output_dir: 缩略图输出目录。
        start_frame: 第一个资产对应的帧号。
        only_set: 是否只设置相机和关键帧，不输出缩略图。
    """
    is_batch = cmds.about(batch=True)

    snap_camera, _ = cmds.camera(name="snapshot_cam")
    cmds.setAttr(snap_camera + ".nearClipPlane", 0.5)
    cmds.setAttr(snap_camera + ".farClipPlane", 100000000)

    if not is_batch:
        mel.eval('setNamedPanelLayout("Single Perspective View")')
        active_panel_name = cmds.playblast(activeEditor=True).split("|")[-1]
        cmds.modelPanel(active_panel_name, edit=True, camera=snap_camera)
        cmds.modelEditor(active_panel_name, edit=True, useDefaultMaterial=False)
        cmds.modelEditor(
            active_panel_name,
            edit=True,
            displayAppearance="smoothShaded",
        )
        cmds.modelEditor(active_panel_name, edit=True, wireframeOnShaded=False)
        cmds.modelEditor(active_panel_name, edit=True, displayTextures=True)
        cmds.modelEditor(active_panel_name, edit=True, shadingModel=True)
        cmds.modelEditor(active_panel_name, edit=True, polymeshes=True)
        cmds.modelEditor(active_panel_name, edit=True, twoSidedLighting=True)
        cmds.modelEditor(active_panel_name, edit=True, displayLights="default")

    for offset, group_name in enumerate(group_list):
        current_frame = start_frame + offset
        cmds.currentTime(current_frame, edit=True)
        cmds.select(group_name, replace=True)
        cmds.viewFit(snap_camera)
        cmds.setKeyframe(snap_camera, time=current_frame)

    end_frame = start_frame + len(group_list) - 1
    all_meshes = [mesh.getParent() for mesh in pm.ls(type="mesh")]
    for mesh in all_meshes:
        for frame in range(start_frame, end_frame + 1):
            pm.setKeyframe(mesh.attr("visibility"), time=frame, value=0)

    for offset, group_name in enumerate(group_list):
        current_frame = start_frame + offset
        mesh_list = pm.listRelatives(
            pm.PyNode(group_name),
            children=True,
            allDescendents=True,
            type="mesh",
        )
        for mesh in mesh_list:
            pm.setKeyframe(
                mesh.getParent().attr("visibility"),
                time=current_frame,
                value=1,
            )

    if only_set:
        return

    print("output_dir: {}".format(output_dir))
    cmds.select(clear=True)
    default_resolution = pm.PyNode("defaultResolution")
    width = int(default_resolution.width.get())
    height = int(default_resolution.height.get())

    try:
        if is_batch:
            _render_batch_snapshots(
                group_list=group_list,
                output_dir=output_dir,
                camera=snap_camera,
                start_frame=start_frame,
                width=width,
                height=height,
            )
        else:
            _playblast_snapshots(
                group_list=group_list,
                output_dir=output_dir,
                start_frame=start_frame,
                end_frame=end_frame,
                width=width,
                height=height,
            )
    finally:
        if cmds.objExists(snap_camera):
            cmds.delete(snap_camera)

        for mesh in all_meshes:
            pm.cutKey(mesh.attr("visibility"))
            mesh.attr("visibility").set(1)
