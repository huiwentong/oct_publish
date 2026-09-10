# -*- coding: utf-8 -*-
import math
import traceback
from pathlib import Path

import maya.api.OpenMaya as om
import pymel.core as pm

from oct.pipeline.shotgun.models import Task
from oct_maya.utils.maya_utils.transform import center_group_to_children


# 单位矩阵：子资产在总场景里的位置由 ASB 组装时的层级决定，这里不写具体 transform
IDENTITY_MATRIX = [1.0, 0.0, 0.0, 0.0,
                   0.0, 1.0, 0.0, 0.0,
                   0.0, 0.0, 1.0, 0.0,
                   0.0, 0.0, 0.0, 1.0]


def get_latest_v_dir_from_task_id(task_id):
    """
    从任务id获取最新的版本目录
    Args:
        task_id: int, 任务id
    Returns:
        str, 版本目录
    """
    sg_task = Task.get(id=task_id)
    latest_sg_version = sg_task.latest_published_version
    return latest_sg_version.get_path(mount_point='publish')


def get_xform_data_from_obj(longname):
    """取节点的 translate/rotate/scale，共 9 个值"""
    center_group_to_children(group=longname)
    node = pm.PyNode(longname)
    trans = list(node.attr('t').get())
    rot = list(node.attr('r').get())
    scl = list(node.attr('s').get())
    return trans + rot + scl


def trs_to_matrix(tx=0.0, ty=0.0, tz=0.0,
                  rx=0.0, ry=0.0, rz=0.0,
                  sx=1.0, sy=1.0, sz=1.0,
                  rotate_order=om.MEulerRotation.kXYZ):
    """
    translate xyz + rotate xyz + scale xyz -> 4x4 matrix

    Args:
        tx, ty, tz: 位移
        rx, ry, rz: 旋转，角度制
        sx, sy, sz: 缩放
        rotate_order: Maya rotate order

    Returns:
        list[float]: 4x4 矩阵展平后的 16 个浮点数
    """
    transform = om.MTransformationMatrix()
    transform.setTranslation(om.MVector(tx, ty, tz), om.MSpace.kTransform)
    # Maya API 需要 radians
    transform.setRotation(om.MEulerRotation(math.radians(rx), math.radians(ry),
                                            math.radians(rz), rotate_order))
    transform.setScale([sx, sy, sz], om.MSpace.kTransform)

    matrix = transform.asMatrix()
    result = []
    for i in range(4):
        for j in range(4):
            result.append(round(matrix.getElement(i, j), 6))
    return result


def get_asb_usd_file(latest_v_dir, asset_name):
    """从子资产的最新版本目录推出它的 asb usda 路径（不带版本号）"""
    publish_root = Path(latest_v_dir)
    return str(publish_root.parent.parent / 'asb' / '{0}.usda'.format(asset_name))


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    获取asb资产的components数据
    """
    # 为 ASB 收集要组装进来的 component 清单，写入 process_data['comps_data']，
    # 由 create_asb_all_usd 交给 step_pub_usds.AsbStepUsd 生成 usda。
    # 仅农场端使用。
    try:
        if process_data['entity_asset_type'] != 'ASB':
            return

        parent_asset_name = process_data['entity_name']
        comps_data = {}

        # sub_assets_data 形如
        # [{"longname": "|miumodong_all|nmd_yuanjing|nmd_yj_shitou", "model_task_id": 145696}, ...]
        for asset in process_data['sub_assets_data']:
            longname = asset['longname']
            asset_name = longname.split('|')[-1]
            model_task_id = asset['model_task_id']

            sub_asset_longname = '|' + parent_asset_name + longname.split(parent_asset_name)[-1]
            level_path = sub_asset_longname.replace('|', '/')
            latest_v_dir = get_latest_v_dir_from_task_id(task_id=model_task_id)

            comps_data[level_path] = {
                'usd_path': level_path,
                'usd_file': get_asb_usd_file(latest_v_dir=latest_v_dir, asset_name=asset_name),
                'transform': {'xform': IDENTITY_MATRIX},
                'visible': 'inherited',
                'component_name': level_path.replace('/', '.')[1:],
            }

        # env_assets_data 来自 ASB场景拆分管理器 的 ENV 占位，形如
        # [{"longname": "|city_all|city_env_shan", "asset_name": "city_env_shan",
        #   "asset_id": 3206, "usd_file": "I:/.../asb/city_env_shan.usda"}, ...]
        # 占位组在场景里是个空组，这里直接按它的层级路径引用 ENV 资产的 usda。
        # 资产还没发布时 usd_file 不存在，USD 只告警不报错，等它发布完自动生效。
        for env_asset in process_data.get('env_assets_data', []):
            longname = env_asset['longname']
            env_longname = '|' + parent_asset_name + longname.split(parent_asset_name)[-1]
            level_path = env_longname.replace('|', '/')

            comps_data[level_path] = {
                'usd_path': level_path,
                'usd_file': env_asset['usd_file'],
                'transform': {'xform': IDENTITY_MATRIX},
                'visible': 'inherited',
                'component_name': level_path.replace('/', '.')[1:],
            }

        process_data['comps_data'] = comps_data
        logger.info(u"收集到 {0} 个 component: {1}".format(
            len(comps_data), list(comps_data.keys())))

    except:
        return traceback.format_exc()
