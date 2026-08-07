
import os
import shutil
import traceback
import json
import hou
from oct.pipeline.path_acs import unlock_path, lock_path, make_dirs, remove

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
复制cfx cache 文件到i盘
    """
    try:
        v_comp_dir = process_data['version_dir'] + '/components'
        if os.path.exists(v_comp_dir):
            remove(v_comp_dir)

        while os.path.exists(v_comp_dir):
            if not os.path.exists(v_comp_dir):
                break

        make_dirs(v_comp_dir)
        unlock_path(v_comp_dir, True)


        for k, v in submit_data['components'].items():
            make_dirs(v_comp_dir+f'/{k}')
            if v.get('cloth'):
                ori_usd_file = v.get('cloth')
                usd_name = os.path.basename(ori_usd_file)
                new_usd_path = v_comp_dir+f'/{k}/{usd_name}'
                shutil.copy(ori_usd_file, new_usd_path)
            if v.get('hair'):
                ori_curves = v.get('hair')
                ori_base = os.path.dirname(ori_curves) + '/base.abc'
                print(ori_base)

                new_curves = v_comp_dir+f'/{k}/curves'
                new_base = v_comp_dir + f'/{k}/base.abc'
                shutil.copytree(ori_curves, new_curves)
                shutil.copy(ori_base, new_base)
            upstream = v.get('upstream')
            up_dict = {k: {}}
            for i in upstream.split(','):
                up_dict[k][i.split(': ')[0]] = i.split(': ')[1]

            up_json = v_comp_dir+f'/{k}/upstream.json'
            with open(up_json, 'w', encoding='utf-8') as f:
                json.dump(up_dict, f, ensure_ascii=False, indent=4)

    except:
        return traceback.format_exc()


