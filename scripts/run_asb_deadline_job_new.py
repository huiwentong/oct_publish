# -*- coding: utf-8 -*-
"""
ASB 拆分发布 —— 农场端子资产发布脚本（新架构版）

由 oct_publish 的 asb_split/process/submit_asb_deadline_task.py 提交到 Deadline
每个拆分出来的子资产一个任务：

    rez-env maya-2024 oct_maya oct_publish -- mayapy run_asb_deadline_job_new.py <job_json>

该文件是一个备份 实际生产环节中脚本位置在 Z:/TD/pipeline/scripts/run_asb_deadline_job_new.py
"""
import maya.standalone
maya.standalone.initialize(name='python')

import importlib
import json
import os
import sys

import maya.cmds as cmds
import pymel.core as pm

from oct.pipeline import path_acs
from oct.pipeline.shotgun.models import Task

from publish_core.log.core import PublishLog


# 按顺序执行的组件，(type, name) 对应
# publish_components/components/<type>/process/<name>.py
PROCESS_LIST = [
    ('gen',       'create_v_dir'),
    ('gen',       'copy_preview_to_v_dir'),
    ('asb_split', 'standard_structure'),
    ('asb_split', 'group_align_cleanup'),
    ('asb_split', 'get_asb_componts_data'),
    ('asb_split', 'clean_unused_materials'),
    ('asb_split', 'copy_asb_asset_images'),
    ('asb_split', 'save_as_from_source'),
    ('asb_split', 'replace_img_and_save'),
    ('asb_split', 'create_asb_all_usd'),
    ('gen',       'lock_v_dir'),
    ('gen',       'sym_link_no_num_version'),
    ('gen',       'create_sg_version'),
]

# 打了「Maya场景」标签的 ASB 拆出来的 PROP 子资产，按 mod 环节发布。
# 只有 PROP 适用：standard_structure 会把 PROP 整理成 |Root_grp|Geo_grp|high，
# 正是 mod 组件假设的层级；ASB 类型子资产保持自身层级，套不上，仍走 PROCESS_LIST。
PROCESS_LIST_MOD = [
    ('gen',       'create_v_dir'),
    ('gen',       'copy_preview_to_v_dir'),
    ('asb_split', 'standard_structure'),
    ('asb_split', 'group_align_cleanup'),
    ('mod',       'unlock_normal_and_soften_edge'),
    ('maya_gen',  'clean_scene'),
    ('maya_gen',  'clean_asset_scene'),
    ('mod',       'clean_mod_scene'),
    ('maya_gen',  'maya_version_attr'),
    ('maya_gen',  'asset_mesh_xml'),
    ('maya_gen',  'copy_asset_images'),
    ('mod',       'export_asset_ma'),
    ('mod',       'export_asset_usd'),
    ('mod',       'update_asset_poly_cnt'),
    ('gen',       'create_manifest_file'),
    ('gen',       'lock_v_dir'),
    ('gen',       'sym_link_no_num_version'),
    ('gen',       'create_sg_version'),
    ('mod',       'auto_gener_low_usd'),
]

# gen_asb_deadline_job 写进 job json 的值，和 publish_components.utils.sg_helper
# 的 MAYA_SCENE_TAG 对应。这里不 import sg_helper：农场端要少拉依赖，
# 而且这个值来自 json 快照，不该再回头查 SG
MAYA_SCENE_KIND = 'maya_scene'


def pick_process_list(job_data):
    """按资产类别和类型选发布流程。

    Args:
        job_data: dict, gen_asb_deadline_job 写出的 *.deadline_job.json
    Returns:
        (list, str) 组件列表和流程名，流程名只用于日志
    """
    if job_data.get('asset_kind') == MAYA_SCENE_KIND and job_data['asset_type'] == 'PROP':
        return PROCESS_LIST_MOD, 'mod'
    return PROCESS_LIST, 'asb'

# 农场自动发布出来的版本固定用「正式」标签，描述也固定
PUBLISH_TAG_ID = 283          # 283 = 正式
PUBLISH_DESCRIPTION = 'Deadline 自动发布ASB模型版本'


def is_main_asb(longname):
    """通过 longname 判断是否是主 asb 资产（只有一层，即场景最顶层）"""
    return longname.count('|') == 1


def send_dd_message(user, message):
    """
    发送钉钉消息
    Args:
        user: dict {'type': 'HumanUser', 'id': 123}
        message: str
    Returns:
        None
    """
    import requests

    from oct.pipeline.shotgun.models import HumanUser

    sg_user = HumanUser.get(id=user['id'], fields=['sg_dingtalk_id'])

    url = "http://192.168.20.217:8080/ding/msg/simple?user_id={0}".format(
        sg_user.sg_dingtalk_id)
    data = {'title': 'Message', 'text': message}

    response = requests.post(url, data=json.dumps(data), timeout=15)
    if response.status_code == 200:
        print('send message to {0} success'.format(sg_user.login))
    else:
        print('send message to {0} failed'.format(sg_user.login))
        print(response.text)


def build_process_data(job_data):
    """
    构造组件需要的 process_data，等价于老版的 FakeDialog。

    场景必须已经打开 —— root 是 PyNode，依赖当前场景。

    Args:
        job_data: dict, gen_asb_deadline_job 写出的 *.deadline_job.json
    Returns:
        dict, process_data
    """
    sg_task = Task.get(id=job_data['model_task_id'])

    entity_name = job_data['asset_name']
    asset_type = job_data['asset_type']
    step_short_name = sg_task.step.short_name.lower()

    # 发布根目录
    publish_root = path_acs.old_get_path(mount_point='publish',
                                         show_name=sg_task.project.name.upper(),
                                         entity_type='Task',
                                         id=sg_task.id)
    if not os.path.exists(publish_root):
        path_acs.make_dirs(publish_root)

    # 版本号取 SG 上已有的最大值 +1
    version_num = 0
    for v in sg_task.versions():
        if v.version_number > version_num:
            version_num = v.version_number
    version_num = str(version_num + 1).zfill(3)

    version_key = '{0}.{1}.{2}'.format(entity_name, step_short_name, sg_task.content)
    version_name = '{0}.v{1}'.format(version_key, version_num)
    version_dir = os.path.join(publish_root, version_name)

    return {
        # ── 任务 / 实体 ──
        'task_id': sg_task.id,
        'task_name': sg_task.content,
        'user': job_data['user'],
        'entity_name': entity_name,
        'entity_id': job_data['asset_id'],
        'entity_asset_type': asset_type,
        'step_name': step_short_name,
        'project_name': sg_task.project.name,
        'project_id': sg_task.project.id,

        # ── 场景层级 ──
        # standard_structure 可能会把 PROP 重新挂到 |Root_grp 下并覆盖这个键
        'root': pm.PyNode(job_data['longname']),

        # ── 路径 ──
        'publish_root': publish_root,
        'version_key': version_key,
        'version_num': version_num,
        'version_name': version_name,
        'version_dir': version_dir,
        'version_dir_no_num': os.path.join(publish_root, version_key),
        'v_dir_preview': os.path.join(version_dir, 'preview', version_name + '.mov'),
        'v_dir_imgs': os.path.join(version_dir, 'sourceimages'),
        'v_dir_usd': os.path.join(version_dir, 'usd'),
        'v_dir_ma_file': os.path.join(version_dir, entity_name + '.ma'),

        # ── 发布表单 ──
        'preview_paths': [job_data['thumb_file']],
        'comment': PUBLISH_DESCRIPTION,
        'auto_description': {},
        'publish_type': 'Publish',
        'publish_tag_id': PUBLISH_TAG_ID,
        'is_deadline_job': True,

        # ── ASB 拆分专用 ──
        'is_main_asb_asset': is_main_asb(job_data['longname']),
        'sub_assets_data': job_data['sub_assets_data'],
        'env_assets_data': job_data.get('env_assets_data', []),
        'comps_data': {},
    }


def main(job_data):
    logger = PublishLog(name='ASB_DEADLINE')

    # 打开拆分出来的总场景
    cmds.file(job_data['source_file'], open=True, force=True)
    logger.info('>>>> File opened: {0}'.format(job_data['source_file']))

    process_data = build_process_data(job_data)
    submit_data = {}
    user = job_data['user']

    process_list, flow_name = pick_process_list(job_data)
    logger.info('>>>> Publishing {0} ({1}) -> {2} [flow: {3}]'.format(
        process_data['entity_name'],
        process_data['entity_asset_type'],
        process_data['version_dir'],
        flow_name))

    for ctype, name in process_list:
        module_path = 'publish_components.components.{0}.process.{1}'.format(ctype, name)
        module = importlib.import_module(module_path)

        doc_lines = (module.main.__doc__ or '').strip().splitlines()
        desc = doc_lines[0].strip() if doc_lines else name
        logger.info('>>>> Run process: {0}/{1} - {2}'.format(ctype, name, desc))

        result = module.main(submit_data, process_data, None, logger)
        if result:
            raise RuntimeError('ASB组件失败: {0}/{1}\n{2}'.format(ctype, name, result))

    logger.info('>>>> All processes done!')


def run_job(job_data):
    """执行发布并返回进程退出码；通知失败不改变发布结果。"""
    logger = PublishLog(name='ASB_DEADLINE')
    exit_code = 0
    message = None
    try:
        main(job_data)
    except Exception:
        import traceback
        logger.error(traceback.format_exc())
        exit_code = 1
        message = 'ASB拆分任务失败: {0}，请查看 Deadline 日志'.format(job_data.get('asset_name', ''))
    else:
        if is_main_asb(job_data['longname']):
            message = 'ASB拆分任务完成! 请打开{0}进行检查'.format(job_data['longname'])

    if message:
        try:
            send_dd_message(user=job_data['user'], message=message)
        except Exception as exc:
            logger.error('发送发布通知失败: {0}'.format(exc))
    return exit_code


if __name__ == '__main__':
    exit_code = 1
    try:
        job_json_file = sys.argv[1]
        with open(job_json_file, 'r') as f:
            job_data = json.load(f)
        exit_code = run_job(job_data)
    finally:
        # mayapy 加载过 mtoa 后正常退出会在 finalizing 阶段崩溃并返回 255，
        # 用 os._exit 跳过 finalizing，让退出码只反映发布结果
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(exit_code)
