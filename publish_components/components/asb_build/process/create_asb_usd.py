# -*- coding: utf-8 -*-
import os
import traceback
from oct.data.usd import step_pub_usds

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """根据 ASB Component 数据生成版本 USD 和资产入口 USD"""
    try:
        components = process_data['asb_components']
        if not components:
            raise RuntimeError('缺少 ASB Component 数据，不能生成空发布')
        result = step_pub_usds.AsbStepUsd(
            version_folder=process_data['version_dir'], components=components,
            task_id=process_data['task_id'])
        outputs = [result.version_usda_file, result.step_usda_file,
                   result.asb_usda_file, result.no_tex_asb_usda_file]
        for path in outputs:
            if not os.path.isfile(path) or os.path.getsize(path) == 0:
                raise RuntimeError('USD 发布文件不存在或为空: ' + path)
        process_data['asb_usd_files'] = outputs
        logger.info('ASB USD 导出完成')
    except Exception:
        return traceback.format_exc()
