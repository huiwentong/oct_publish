# -*- coding: utf-8 -*-

import os
import subprocess
import traceback

import maya.utils as utils
from oct.pipeline.task_context import TaskContext
from oct_maya.tools.utils.oct_asset_turntable.core.api import TurntableAPI
from publish_components.utils.sg_helper import get_asset_kind, MAYA_SCENE_TAG, UE_SCENE_TAG


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """提交 Deadline 任务：Turntable。"""

    frame_start = 1
    frame_end = 200
    default_frame_step = 4

    def log(level, message):
        if logger is not None:
            log_method = getattr(logger, level, None)
            if callable(log_method):
                log_method(message)
                return
        print('[Turntable] {}'.format(message))

    def get_turntable_frame_step():
        """读取 Interface 的 Step；无值时使用 4，并返回数据来源。"""
        submit_values = submit_data if isinstance(submit_data, dict) else {}
        process_values = process_data if isinstance(process_data, dict) else {}

        sources = [
            ('submit_data', submit_values),
            ('submit_data.input_form', submit_values.get('input_form')),
            ('process_data', process_values),
            ('process_data.input_form', process_values.get('input_form')),
        ]

        for source_name, values in sources:
            if not isinstance(values, dict) or 'turntable_frame_step' not in values:
                continue

            raw = values['turntable_frame_step']
            if isinstance(raw, bool) or raw is None:
                raise ValueError('Invalid turntable_frame_step from {}: {!r}'.format(source_name, raw))

            value_text = str(raw).strip()
            if not value_text.isdigit():
                raise ValueError('turntable_frame_step must be an integer, got {!r} from {}'.format(raw, source_name))

            step = int(value_text)
            if not 1 <= step <= 200:
                raise ValueError('turntable_frame_step must be 1-200, got {}'.format(step))

            return step, source_name

        return default_frame_step, 'default'

    def submit_to_deadline_turntable(tc):
        proj_name = tc.project_name.lower()
        asset_name = tc.entity_name
        dept = tc.step.short_name.lower()

        if dept == 'mod':
            version_dir = process_data.get('version_dir')
            output_dir = version_dir + '/preview/origin'
            tt_api = TurntableAPI()
            info = utils.executeInMainThreadWithResult(
                lambda: tt_api.render_all_cameras(
                    output_dir=output_dir,
                    step=dept,
                    data=None,
                    asset_name=asset_name,
                    template_key='TT_3points',
                    remove_template=True,
                )
            )
            log('info', info.get('message'))
            return

        task = tc.task_name
        frame_step, source = get_turntable_frame_step()
        log('info', 'Turntable frames: {}-{}x{} (source: {})'.format(
            frame_start, frame_end, frame_step, source
        ))
        if source == 'default':
            log('warning', 'Interface step not found in submit_data/process_data; using default 4')

        env_dict = os.environ.copy()
        env_dict['REZ_CONFIG_FILE'] = r'\\192.168.15.15\pipeline\config\rezconfig.py'

        cmd = [
            'rez-env',
            'oct_turntable_to_deadline',
            '--',
            'tt_to_deadline2',
            str(proj_name),
            str(asset_name),
            str(dept),
            str(task),
            '--frame-start', str(frame_start),
            '--frame-end', str(frame_end),
            '--frame-step', str(frame_step),
        ]

        log('info', 'Submit Turntable: {}'.format(' '.join(cmd)))
        subprocess.run(
            cmd,
            check=True,
            env=env_dict,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
        )
        log('debug', 'Turntable submitted: {} {} {} {} (step={})'.format(
            proj_name, asset_name, dept, task, frame_step
        ))

    try:
        task_id = process_data.get('task_id')
        tc = TaskContext(task_id) or TaskContext.from_env()
        formated_mov_dic = process_data.get('formated_mov_dic')

        # Maya 场景 / UE 场景资产不做 Turntable。
        is_scene_asset = get_asset_kind(task_id) in (MAYA_SCENE_TAG, UE_SCENE_TAG)
        asset_type = str(tc.entity.sg_asset_type or '').lower()

        if not formated_mov_dic and not is_scene_asset and asset_type in ('chr', 'ch', 'prop', 'prp'):
            submit_to_deadline_turntable(tc)

    except Exception:
        error = traceback.format_exc()
        log('error', error)
        return error
