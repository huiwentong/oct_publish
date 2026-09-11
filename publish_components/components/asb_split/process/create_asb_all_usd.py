# -*- coding: utf-8 -*-
import os
import subprocess
import tempfile
import traceback

from oct.data.usd import step_pub_usds


# 导出脚本模板：mayaUSDExport 在当前 mayapy 会话里跑容易受场景状态影响，
# 老流程一直是另起一个干净的 maya 进程来导，这里保持一致
_EXPORT_CODE = """# -*- coding: utf-8 -*-
import os
import sys
import traceback

# 每一步都打标记，失败时主进程把这些行带回错误信息里，方便定位卡在哪
def _log(msg):
    print('>>>> [usd_export] ' + msg)
    sys.stdout.flush()

try:
    import pymel.core as pm
    import maya.cmds as cmds
    _log('loading plugins')
    pm.loadPlugin('mayaUsdPlugin', quiet=True)
    pm.loadPlugin('mtoa', quiet=True)
    _log('opening ' + r'{ma}')
    cmds.file(r'{ma}', o=True, f=True)
    _log('file opened, top-level: ' + str(cmds.ls(assemblies=True)))
    n_geogrp = pm.PyNode('{longname}')
    if not os.path.isdir(r'{v_dir_usd}'):
        os.makedirs(r'{v_dir_usd}')
    usd_path = r'{v_dir_usd}' + r'/high.usd'
    if os.path.isfile(usd_path):
        os.remove(usd_path)
    _log('exporting ' + usd_path)
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
    ok = os.path.isfile(usd_path) and os.path.getsize(usd_path) > 0
    _log('export done, file ok: ' + str(ok))
    exit_code = 0 if ok else 1
except Exception:
    _log('EXPORT FAILED')
    traceback.print_exc()
    sys.stdout.flush()
    exit_code = 1

# mayapy 加载过 mtoa 后正常退出会在 finalizing 阶段崩
# (Fatal Python error: PyThreadState_Get ...) 并返回 255，
# 与导出成功与否无关。用 os._exit 跳过 finalizing，让退出码只反映导出结果
os._exit(exit_code)
"""


def export_usd_with_command(maya_file, v_dir_usd, longname, logger=None):
    """另起一个 mayapy 进程导出 high.usd"""
    code = _EXPORT_CODE.format(ma=maya_file, v_dir_usd=v_dir_usd, longname=longname)

    # 模板里有中文注释，必须按 UTF-8 写盘：默认编码在中文 Windows 上是 cp936，
    # mayapy 按 UTF-8 解析源码会在解析阶段直接 SyntaxError（退出码 1，且没有 Traceback）
    with tempfile.NamedTemporaryFile('w', delete=False, suffix='.py', encoding='utf-8') as f:
        f.write(code)
        script_path = f.name

    cmd = 'rez-env maya-2024 oct_maya -c "mayapy.exe {0}"'.format(script_path)
    if logger:
        logger.info(u"导出 USD 命令: {0}".format(cmd))

    # 子进程输出落盘，而不是混进主进程的 stdout —— Deadline 日志里 Arnold 的插件列表
    # 会把关键报错淹掉。失败时把标记行和 traceback 带回错误信息
    log_path = script_path + '.log'
    with open(log_path, 'w', encoding='utf-8', errors='replace') as log_f:
        sp = subprocess.Popen(cmd, stdout=log_f, stderr=subprocess.STDOUT)
        sp.wait()

    usd_path = os.path.join(v_dir_usd, 'high.usd')
    file_ok = os.path.isfile(usd_path) and os.path.getsize(usd_path) > 0

    if sp.returncode != 0 or not file_ok:
        # 只挑出我们自己打的标记行和 Python traceback，跳过 Arnold / pymel 的启动噪音
        try:
            with open(log_path, 'r', encoding='utf-8', errors='replace') as log_f:
                lines = log_f.read().splitlines()
        except Exception:
            lines = []
        keep, in_tb = [], False
        for line in lines:
            if line.startswith('>>>> [usd_export]') or line.startswith('Traceback'):
                in_tb = line.startswith('Traceback')
                keep.append(line)
            elif in_tb:
                keep.append(line)
                if line and not line.startswith(' '):
                    in_tb = False
        # 一条标记都没有，说明脚本在解析阶段就挂了（如 SyntaxError，不带 Traceback 头）
        # 或 rez / mayapy 根本没起来，此时直接带上日志末尾
        if not keep:
            keep = [u'(未捕获到导出标记，脚本可能未执行到导出逻辑，以下为日志末尾)'] + lines[-30:]
        raise RuntimeError(
            u"USD 导出失败，退出码: {0}，文件存在: {1}\n完整日志: {2}\n{3}".format(
                sp.returncode, file_ok, log_path, '\n'.join(keep[-40:])))

    if logger:
        logger.info(u"high.usd 已生成: {0} ({1} bytes)".format(usd_path, os.path.getsize(usd_path)))
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
