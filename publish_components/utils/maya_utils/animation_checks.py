# coding=utf-8
"""动画检查的可复用场景逻辑，由组件在 Maya 主线程调用。"""
import json
import math
import os

import maya.cmds as cmds


def duplicated_cache_nodes() -> dict[tuple[str, str], list[str]]:
    """查找 cache_grp 下同父级、忽略 namespace 后重名的非引用物体。

    Returns:
        (短名, 父路径) 到重复物体完整路径的映射。
    """
    group = '|lay|cache_grp'
    if not cmds.objExists(group):
        return {}
    shapes = cmds.ls(group, dag=True, long=True, type='shape') or []
    transforms = sorted({shape.rsplit('|', 1)[0] for shape in shapes})
    nodes = {}
    for node in transforms:
        if cmds.referenceQuery(node, isNodeReferenced=True):
            continue
        parent, leaf = node.rsplit('|', 1)
        key = (leaf.rsplit(':', 1)[-1], parent)
        nodes.setdefault(key, []).append(node)
    return {key: paths for key, paths in nodes.items() if len(paths) > 1}


def check_reference_apose() -> str:
    """按旧 MK2 ani 规则检查角色绑定 A-Pose，并恢复当前时间。

    保留旧规则：仅 ani.animation 文件，50 帧比对 controller_data.json，
    0–51 帧至少有一个控制器关键帧；MotionSystem 绑定只校验关键帧。

    Returns:
        失败原因，成功或不适用时返回空字符串。
    """
    if 'ani.animation' not in cmds.file(q=True, sn=True, shn=True):
        return ''
    original_time = cmds.currentTime(query=True)
    errors = []
    try:
        cmds.currentTime(50)
        for root in cmds.ls('*:Root_grp') or []:
            if not cmds.referenceQuery(root, isNodeReferenced=True):
                continue
            ref_path = cmds.referenceQuery(root, filename=True).replace('rigging_nemo', 'rigging')
            if 'asset/chr' not in ref_path.replace('\\', '/'):
                continue
            namespace = root.rsplit('|', 1)[-1].rsplit(':', 1)[0]
            if 'rig.rigging' not in ref_path:
                errors.append('{}: 引用的不是绑定发布文件 -> {}'.format(namespace, ref_path))
                continue
            data_path = os.path.join(os.path.dirname(ref_path), 'controller_data.json')
            if not os.path.isfile(data_path):
                errors.append('{}: 找不到 controller_data.json -> {}'.format(namespace, data_path))
                continue
            with open(data_path, encoding='utf-8') as stream:
                data = json.load(stream)
            controls = {name: values for name, values in data['keyable'].items()
                        if name.endswith(('_ctrl', '_CTL')) and cmds.objExists(namespace + ':' + name)}
            if not any(cmds.keyframe(namespace + ':' + name, q=True, t=(0, 51)) for name in controls):
                errors.append('{}: 0–51 帧所有控制器均无关键帧，需制作 A-Pose'.format(namespace))
                continue
            if cmds.objExists(namespace + ':MotionSystem'):
                continue
            excluded = {
                'master_ctrl', 'masterA_ctrl', 'torso_ctrl', 'torsoA_ctrl',
                'l_foot_ik_ctrl', 'r_foot_ik_ctrl', 'l_wrist_ik_ctrl', 'r_wrist_ik_ctrl',
                'l_wristRot_ik_ctrl', 'r_wristRot_ik_ctrl',
                'l_shoulderpole_ctrl', 'r_shoulderpole_ctrl', 'l_hippole_ctrl',
                'm_spine_ik_ctrl', 'm_spine1_ik_ctrl', 'm_chest_ik_ctrl',
            }
            if 'xiaokongkong' in namespace:
                excluded = {
                    'master_ctrl', 'masterA_ctrl', 'torso_ctrl', 'torsoA_ctrl',
                    'l_foot_ikC_ctrl', 'r_foot_ikC_ctrl', 'l_wrist_ikC_ctrl', 'r_wrist_ikC_ctrl',
                    'l_shoulderpole_ikC_ctrl', 'r_shoulderpole_ikC_ctrl', 'l_hippole_ikC_ctrl',
                    'm_spine_ik_ctrl', 'm_spine1_ik_ctrl', 'm_chest_ik_ctrl',
                }
            bad_attr = ''
            for control, values in controls.items():
                if control in excluded or any(attr in values for attr in ('global', 'FKIKBlend', 'follow')):
                    continue
                for attr, expected in values.items():
                    if 'rotateOrder' in attr:
                        continue
                    plug = namespace + ':' + control + '.' + attr
                    actual = cmds.getAttr(plug)
                    if math.fabs(actual - expected) > 0.001:
                        bad_attr = '{} 当前值 {}，A-Pose 应为 {}'.format(plug, actual, expected)
                        break
                if bad_attr:
                    break
            if bad_attr:
                errors.append('{}: A-Pose 数值检查不通过 -> {}'.format(namespace, bad_attr))
        return '\n'.join(errors)
    finally:
        cmds.currentTime(original_time)
