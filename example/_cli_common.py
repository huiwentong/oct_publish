# -*- coding: utf-8 -*-
"""
example 下各环节 CLI 示例的公共部分。

从工程文件名解析 项目 / 实体 / 环节 / 任务 / 版本号，反查 SG 任务 ID，
再构造 PublishCli 执行非 GUI 发布。各环节示例只需要填工程文件、预览文件和提交类型。

工程文件路径约定：

    .../projects/<项目>/<shot|asset>/.../<实体>.<环节>.<任务>.v###.ma
    例：W:/projects/mk2/shot/s99/s990120/lay/maya/s990120.lay.rough_layout.v013.ma
        W:/projects/tdtest/asset/asb/temp_a_all/mod/maya/temp_a_all.mod.model.v009.ma
"""
import os
import re
from dataclasses import dataclass

from publish_core.cli import PublishCli, PublishType
from publish_core.database.core import FastSg
from publish_core.database.entity import get_step_short_name, get_user


# 283=正式 971=过程 282=测试
# 示例统一用测试标签，确认流程无误后再改成 283。
PUBLISH_TAG_ID = 282

_WORK_FILE_RE = re.compile(
    r'^(?P<entity>[^.]+)\.(?P<step>[^.]+)\.(?P<task>[^.]+)\.(?P<version>v\d{3})\.(?P<ext>ma|mb)$',
    re.IGNORECASE,
)


@dataclass(frozen=True)
class WorkFile:
    """从工程文件路径解析出来的发布上下文"""
    path: str
    project: str
    entity_type: str  # Shot / Asset
    entity: str
    step: str
    task: str
    version: str  # 带 v 前缀，如 v013

    @property
    def version_name(self) -> str:
        return f'{self.entity}.{self.step}.{self.task}.{self.version}'


def parse_work_file(path: str) -> WorkFile:
    """按 work 路径规则解析工程文件，路径或文件名不合规范直接抛错。"""
    norm = path.replace('\\', '/')
    if not os.path.isfile(norm):
        raise FileNotFoundError(f'工程文件不存在: {path}')

    match = _WORK_FILE_RE.match(os.path.basename(norm))
    if not match:
        raise ValueError(f'工程文件名不符合 <实体>.<环节>.<任务>.v###.ma 规范: {os.path.basename(norm)}')

    parts = norm.split('/')
    try:
        project = parts[parts.index('projects') + 1]
        kind = parts[parts.index('projects') + 2].lower()
    except (ValueError, IndexError):
        raise ValueError(f'路径里找不到 projects/<项目>/<shot|asset> 结构: {path}') from None
    if kind not in ('shot', 'asset'):
        raise ValueError(f'projects/<项目>/ 之后应该是 shot 或 asset，当前是 {kind}: {path}')

    return WorkFile(
        path=norm,
        project=project,
        entity_type='Shot' if kind == 'shot' else 'Asset',
        entity=match['entity'],
        step=match['step'].lower(),
        task=match['task'],
        version=match['version'].lower(),
    )


def find_task_id(work: WorkFile) -> int:
    """按 项目 + 实体 + 任务名 + 环节短名 反查 SG 任务，必须唯一命中。

    环节短名用 get_step_short_name 解析（description 优先），和版本名规则保持一致，
    这样镜头 lay 环节能用文件名里的 'lay' 匹配到 short_name 为 'ly' 的 Step。
    """
    sg = FastSg().client
    tasks = sg.find(
        'Task',
        [
            ['entity', 'type_is', work.entity_type],
            [f'entity.{work.entity_type}.code', 'is', work.entity],
            ['content', 'is', work.task],
            ['sg_status_list', 'is_not', 'omt'],
        ],
        ['id', 'content', 'step', 'project.Project.name', 'project.Project.code',
         'step.Step.short_name', 'step.Step.description'],
    )

    matched = []
    for task in tasks:
        proj_names = {str(task.get('project.Project.name') or '').lower(),
                      str(task.get('project.Project.code') or '').lower()}
        if work.project.lower() not in proj_names:
            continue
        step = {'id': task['step']['id'],
                'short_name': task.get('step.Step.short_name'),
                'description': task.get('step.Step.description')}
        if get_step_short_name(step) != work.step:
            continue
        matched.append(task)

    if len(matched) != 1:
        raise RuntimeError(
            f'按 {work.project} / {work.entity} / {work.step} / {work.task} 查到 {len(matched)} 个任务，'
            f'无法确定发布任务: {[t["id"] for t in matched]}'
        )
    return matched[0]['id']


def run_publish(label: str, ma_file: str, preview_file: str, publish_type: PublishType,
                extra_form: dict | None = None) -> int:
    """解析工程文件、反查任务，执行非 GUI 发布；成功返回 0，失败返回 1。

    Args:
        label: 日志里显示的环节名称，如 "镜头 Layout"。
        ma_file: 工程文件路径，版本号从文件名解析。
        preview_file: 预览文件路径。
        publish_type: PublishType.DAILY 或 PublishType.PUBLISH。
        extra_form: 环节额外的表单项，如 blk / ani 的 is_split_task。
    """
    work = parse_work_file(ma_file)
    preview = preview_file.replace('\\', '/')
    if not os.path.isfile(preview):
        raise FileNotFoundError(f'预览文件不存在: {preview_file}')

    task_id = find_task_id(work)
    input_form = {'ma_file': work.path}
    input_form.update(extra_form or {})

    # Dailies 和 Publish 都通过 mayapy 打开工程文件执行：
    # Dailies 组的检查项里 version_up_going 的 Fix 引用了 pymel，会被脚本生成器提到最前面，
    # 纯 python 的 cmd 模式目前跑不起来，统一走 Maya 环境最稳。
    publish_cli = PublishCli(
        user=get_user(),
        task_id=task_id,
        gui=False,
        publish_type=publish_type,
        comment=f'oct_publish CLI {publish_type.value} 提交 {work.version_name}',
        publish_tag_id=PUBLISH_TAG_ID,
        version_num=work.version,
        dcc='Maya',
        dcc_file=work.path,
        preview_paths=[preview],
        input_form=input_form,
    )

    log = publish_cli.log
    log.info(f'任务 {task_id} / 版本 {work.version_name} / 模式 {publish_type.value}')
    log.info(f'CLI 初始化完成，开始执行{label} {publish_type.value} 发布。')
    publish_cli.interface.run_in_cli()

    if publish_cli.interface.all_complete:
        log.info(f'{label} {publish_type.value} 发布执行完成。')
        return 0

    log.error(f'{label} {publish_type.value} 发布失败，请检查日志。')
    return 1
