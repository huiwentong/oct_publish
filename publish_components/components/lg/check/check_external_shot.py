# -*- coding: utf-8 -*-
import traceback

from publish_components.utils.lgt_cmp_publish.checks import check_external_shot
from publish_components.utils.lgt_cmp_publish.result import to_framework_status


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查 ShotGrid 镜头是否填写灯光审核所需的外部镜头号。"""
    try:
        return to_framework_status(check_external_shot(process_data), logger)
    except Exception:
        return traceback.format_exc()
