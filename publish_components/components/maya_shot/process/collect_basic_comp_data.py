# -*- coding: utf-8 -*-
import importlib
import traceback

import maya.cmds as cmds
import maya.utils as utils

from oct.pipeline.shotgun.models import Asset, Version
from oct.pipeline.task_context import TaskContext
from oct_maya.tools.lay.usd_lay_manager_new.core import is_old_asb_architecture
from oct_maya.utils.maya_utils import pipe
from publish_components.utils.maya_utils import asb_build


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    收集镜头 component 信息（引用资产 / ASB Stage 里的资产），写入 process_data['shot_comp_data']
    """
    # 两个来源：
    #   1. 场景里 reference 进来的资产，由 ShotDataGenerator 读取（type='reference'）；
    #      它也会把 assemblyReference 节点收进来（type='assembly'），当前流程不用，过滤掉。
    #   2. |World|asset|asb 下 ASB Stage 引用的资产：旧架构按 AR_<资产名> 组名取，
    #      新架构读 Stage 根 Prim 名；每个资产按 model 任务最新的 Publish 版本补一条 reference 记录。
    #
    # 结果由 export_comp_data 写成 shot_components.json，update_sg_version 用它更新镜头的资产链接，
    # oct_cache_exporter 按每条记录的 to_assemble / ani_status / asset_type 决定缓存输出方式。
    # comp_transform_data 在 lay 环节没有内容，写空 dict 保持 json 结构一致。
    try:
        tc = TaskContext(process_data['task_id'])
        proj_name = tc.project_name
        project = {'type': 'Project', 'id': tc.project_id}

        def asset_type_short(sg_asset_type):
            return (sg_asset_type or '').lower().replace('ch', 'chr').replace('prop', 'prp')

        def latest_publish_version_code(asset_name, task_name):
            """资产某个任务最新的 Publish 版本名，没有返回 None"""
            versions = Version.filter(
                filters=[['project', 'is', project],
                         ['entity', 'name_is', asset_name],
                         ['sg_task', 'name_is', task_name],
                         ['sg_version_type', 'is', 'Publish']],
                fields=['code'],
                order=[{'field_name': 'id', 'direction': 'desc'}], limit=1)
            return versions[0].code if versions else None

        def build_ref_comp(asset_name, task_name):
            """按引用资产的格式构造 comp 记录，缺少资产或 Publish 版本时中断收集。"""
            assets = Asset.filter(filters=[['project', 'is', project], ['code', 'is', asset_name]],
                                  fields=['code', 'sg_asset_type'])
            if not assets:
                raise RuntimeError(u"SG 上找不到资产 {0}，无法完成 component 收集".format(asset_name))
            version_code = latest_publish_version_code(asset_name, task_name)
            if not version_code:
                raise RuntimeError(u"资产 {0} 的 {1} 任务没有 Publish 版本，无法完成 component 收集".format(
                    asset_name, task_name))
            a_type = asset_type_short(assets[0].sg_asset_type)

            return {'asset_name': asset_name,
                    'with_version_num': False,
                    'component_node': '{0}RN'.format(asset_name),
                    'asset_type': a_type,
                    'to_assemble': True,
                    'look_pass': 'default',
                    'namespace': asset_name,
                    'dag_path': 'asset|{0}|{1}:Root_grp'.format(a_type, asset_name),
                    'version': version_code,
                    'ani_status': 'animated',
                    'type': 'reference',
                    'in_frustrum': [0, 0]}

        def collect_scene_data():
            """在 Maya 主线程里读场景：引用 comp、ASB Stage 里的资产名"""

            generator = pipe.ShotDataGenerator()
            comp_dic = {comp: info for comp, info in generator.generate_comp_info().items()
                        if info.get('type') != 'assembly'}

            asb_ar_node_list = []
            if int(cmds.about(v=True)) > 2020 and cmds.objExists('|World|asset|asb'):
                asb_ar_node_list = cmds.listRelatives('|World|asset|asb', c=True) or []

            usd_asset_names = set()
            if is_old_asb_architecture():
                for ar_node in asb_ar_node_list:
                    usd_asset_names.add(ar_node.replace('AR_', ''))
            elif asb_ar_node_list:
                asb_build.init_usd()
                maya_usd_lib = importlib.import_module('mayaUsd.lib')
                UsdGeom = importlib.import_module('pxr.UsdGeom')
                stage = maya_usd_lib.GetPrim(asb_ar_node_list[0]).GetStage()
                for prim in stage.GetPseudoRoot().GetChildren():
                    if prim.IsA(UsdGeom.Xform):
                        usd_asset_names.add(prim.GetName().rstrip('0123456789'))

            return comp_dic, sorted(usd_asset_names)

        comp_dic, usd_asset_names = utils.executeInMainThreadWithResult(collect_scene_data)

        # ASB 里的资产按 model 任务的 Publish 版本记录
        for asset_name in usd_asset_names:
            comp_dic[asset_name] = build_ref_comp(asset_name, 'model')

        # 所有资产收集成功后再写入，避免下游使用不完整结果覆盖镜头资产链接。
        process_data['shot_comp_data'] = comp_dic
        process_data['comp_transform_data'] = {}
        logger.info(u"收集到 {0} 个 component: {1}".format(len(comp_dic), ', '.join(sorted(comp_dic.keys()))))
    except:
        return traceback.format_exc()
