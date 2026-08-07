import os.path
import traceback
from pxr import UsdGeom, Usd, Gf

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
检查cfx cache是否合规！
    """
    try:
        comps = [i for i in submit_data['components'].keys()]

        if len(comps) == 0:
            return '没有可发布的组件！'
        # TODO:这块需要详细再补充一下
        for k,v in submit_data['components'].items():

            curve_file = v.get('hair')
            base_file = os.path.dirname(v.get('hair')) + '/base.abc'
            cloth_file = v.get('cloth')
            if cloth_file:
                if not os.path.exists(cloth_file):
                    return f'组件{k}的cloth文件{cloth_file}不存在！'
                stage = Usd.Stage.Open(v.get('cloth'))
            elif curve_file:
                if not os.path.exists(curve_file):
                    return f'组件{k}的curves文件{curve_file}不存在！'
                if not os.path.exists(base_file):
                    return f'组件{k}的生长面文件{base_file}不存在！'
                pass
    except:
        return traceback.format_exc()
