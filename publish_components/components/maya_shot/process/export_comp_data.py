# -*- coding: utf-8 -*-
import json
import os
import traceback


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    导出镜头 component 信息到版本目录：shot_components.json 与 data/comp_transform.json
    """
    # 依赖 collect_basic_comp_data 写入的 shot_comp_data / comp_transform_data。
    try:
        version_dir = process_data['version_dir']
        shot_comp_data = process_data.get('shot_comp_data')
        if shot_comp_data is None:
            return u"没有收集到镜头 component 信息，请确认 collect_basic_comp_data 已执行"

        data_file_path = version_dir + '/shot_components.json'
        with open(data_file_path, 'w') as f:
            json.dump(shot_comp_data, f, indent=4, ensure_ascii=True)
        logger.info(u"导出 {0}".format(data_file_path))

        data_dir = version_dir + '/data'
        if not os.path.isdir(data_dir):
            os.makedirs(data_dir)
        comp_transform_file_path = data_dir + '/comp_transform.json'
        with open(comp_transform_file_path, 'w') as f:
            json.dump(process_data.get('comp_transform_data', {}), f, indent=4, ensure_ascii=True)
        logger.info(u"导出 {0}".format(comp_transform_file_path))
    except:
        return traceback.format_exc()
