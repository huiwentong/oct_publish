
import traceback
from oct.data.usd import step_pub_usds
from glob import glob


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
生成 cfx xgd 文件
    """
    try:
        v_comp_dir = process_data['version_dir'] + '/components'
        for k, v in submit_data['components'].items():
            xgd_file = v_comp_dir+f'/{k}/hair.xgd'
            if v.get('hair'):
                all_abcs = glob(v_comp_dir+f'/{k}/curves/*.abc')
                step_pub_usds.gener_xgd(xgd_file, all_abcs)
    except:
        return traceback.format_exc()

