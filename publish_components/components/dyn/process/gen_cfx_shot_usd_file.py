
import os
import traceback
import re
from oct.data.usd import step_pub_usds
from publish_core.database.entity import FastSg, SGEntity


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
生成 shot USD文件
    """
    try:
        map = {
            'CH': 'chr',
            'PROP': 'prp',
        }
        sg = FastSg().client
        task = SGEntity('Task', process_data['task_id'])
        v_comp_dir = process_data['version_dir'] + '/components'
        comp_dict = {}
        for k, v in submit_data['components'].items():
            xgd_file = None
            base_file = None
            usd_file = None
            if v.get('hair'):
                xgd_file = v_comp_dir + f'/{k}/hair.xgd'
                base_file = v_comp_dir + f'/{k}/base.abc'
            if v.get('cloth'):
                usd_file = v_comp_dir + f'/{k}/{os.path.basename(v.get("cloth"))}'

            asset_name = re.sub('[\d]*?$', '', k)

            upstream = v.get('upstream')
            hair = [i for i in upstream.split(',') if 'hair' in i][0]
            hair_id = hair.split(': ')[1]
            v_name = sg.find_one('Version', filters=[['id', 'is', int(hair_id)]], fields=['code'])['code']
            hair_pass = v_name.split('.')[-2]

            a_filters = [
                ['code', 'is', asset_name],
                ['project', 'name_is', task.project.code],
            ]
            asset = sg.find_one('Asset', filters=a_filters, fields=['code', 'sg_asset_type'])
            asset_type = asset['sg_asset_type']
            tar_path = f'/world/asset/{map[asset_type]}/{k}'

            comp_dict[tar_path] = {
                'xgd_file': xgd_file,
                'base_file': base_file,
                'usd_file': usd_file,
                'usd_path': tar_path,
                'fur_pass': hair_pass,
                'upstream': v.get('upstream'),
                'transform': None,
                'visible': True,
            }

        step_pub_usds.CfxShotStepUsd(process_data['version_dir'], process_data['task_id'], comp_dict)
    except:
        return traceback.format_exc()


