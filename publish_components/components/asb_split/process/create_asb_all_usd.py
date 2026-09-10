# -*- coding: utf-8 -*-
import os
import subprocess
import tempfile
import traceback

from oct.data.usd import step_pub_usds


# 导出脚本模板：mayaUSDExport 在当前 mayapy 会话里跑容易受场景状态影响，
# 老流程一直是另起一个干净的 maya 进程来导，这里保持一致
_EXPORT_CODE = """
import pymel.core as pm
import maya.cmds as cmds
import os
pm.loadPlugin('mayaUsdPlugin', quiet=True)
pm.loadPlugin('mtoa', quiet=True)
cmds.file(r'{ma}', o=True, f=True)
n_geogrp = pm.PyNode('{longname}')
if not os.path.isdir(r'{v_dir_usd}'):
    os.makedirs(r'{v_dir_usd}')
usd_path = r'{v_dir_usd}' + r'/high.usd'
if os.path.isfile(usd_path):
    os.remove(usd_path)
pm.mayaUSDExport(
    file=usd_path,
    exportRoots=[n_geogrp.name()],
    exportUVs=True,
    exportSkels='none',
    exportSkin='none',
    exportBlendShapes=False,
    exportColorSets=True,
    defaultMeshScheme='none',
    defaultUSDFormat='usdc',
    eulerFilter=False,
    staticSingleSample=False,
    frameStride=1,
    frameSample=0.0,
    parentScope='',
    exportDisplayColor=False,
    shadingMode='useRegistry',
    convertMaterialsTo='UsdPreviewSurface',
    exportInstances=True,
    exportVisibility=True,
    mergeTransformAndShape=False,
    stripNamespaces=True
)
"""


def export_usd_with_command(maya_file, v_dir_usd, longname, logger=None):
    """另起一个 mayapy 进程导出 high.usd"""
    code = _EXPORT_CODE.format(ma=maya_file, v_dir_usd=v_dir_usd, longname=longname)

    with tempfile.NamedTemporaryFile('w', delete=False, suffix='.py') as f:
        f.write(code)
        script_path = f.name

    cmd = 'rez-env maya-2024 oct_maya -c "mayapy.exe {0}"'.format(script_path)
    if logger:
        logger.info(u"导出 USD 命令: {0}".format(cmd))

    sp = subprocess.Popen(cmd)
    sp.wait()
    if sp.returncode != 0:
        raise RuntimeError(u"USD 导出进程失败，退出码: {0}".format(sp.returncode))
    usd_path = os.path.join(v_dir_usd, 'high.usd')
    if not os.path.isfile(usd_path) or os.path.getsize(usd_path) == 0:
        raise RuntimeError(u"USD 导出未生成有效文件: {0}".format(usd_path))
    return sp.returncode


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    导出 ASB 的 USD 文件
    """
    # ASB 导出 high.usd 后再用 comps_data 生成组装用的 asb usda；
    # PROP 只导 high.usd 并生成 mod 的 step usd。仅农场端使用。
    try:
        v_dir_usd = process_data['v_dir_usd']
        version_dir = process_data['version_dir']
        publish_root = process_data['publish_root']
        entity_name = process_data['entity_name']
        asset_type = process_data['entity_asset_type']
        task_id = process_data['task_id']
        v_dir_ma_file = process_data['v_dir_ma_file']

        if not os.path.isdir(v_dir_usd):
            os.makedirs(v_dir_usd)
        usd_path = os.path.join(v_dir_usd, 'high.usd')
        if os.path.isfile(usd_path):
            os.remove(usd_path)

        # 导出前先删掉旧的 step usda，避免 AsbStepUsd 读到上一版的内容
        if asset_type == 'ASB':
            step_usd_path = os.path.join(publish_root, '{0}.asb.usda'.format(entity_name))
            if os.path.exists(step_usd_path):
                logger.info(u"删除 asb 的 step.usda 文件: {0}".format(step_usd_path))
                os.remove(step_usd_path)

        if asset_type == 'ASB':
            root = process_data['root']
            export_usd_with_command(maya_file=v_dir_ma_file,
                                    v_dir_usd=v_dir_usd,
                                    longname=root.longName(),
                                    logger=logger)

            step_pub_usds.AsbStepUsd(
                version_folder=version_dir,
                components=process_data.get('comps_data', {}),
                task_id=task_id,
            )
            logger.info(u"已生成 ASB 的 step usd")

        elif asset_type == 'PROP':
            export_usd_with_command(maya_file=v_dir_ma_file,
                                    v_dir_usd=v_dir_usd,
                                    longname='|Root_grp|Geo_grp',
                                    logger=logger)

            step_pub_usds.ModStepUsd(
                version_folder=version_dir,
                task_id=task_id,
            )
            logger.info(u"已生成 PROP 的 step usd")

        else:
            logger.warning(u"资产类型 {0} 不做 USD 导出".format(asset_type))

    except:
        return traceback.format_exc()
