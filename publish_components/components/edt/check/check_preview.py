import traceback
import os
from publish_core.database.entity import SGEntity


def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
检查预览图是否正确
    """
    try:
        movs:list = process_data.get('preview_paths')
        if len(movs) > 1:
            return "剪辑提交单场次daily，只能提交一个视频"

        mov = movs[0]
        if not os.path.exists(mov):
            return f"视频文件不存在：{mov}"

        if not os.path.isfile(mov):
            return f"路径不是文件：{mov}"

        if os.path.getsize(mov) == 0:
            return f"视频文件为空：{mov}"
        if mov.replace('\\', '/').lower() != 'z:/TD/pipeline/resource/oct_publish/edt_preview.png'.lower():
            return f"发布下游的剪辑预览不可以手动改变！必须使用工具默认图片"
        


    except:
        return traceback.format_exc()




# def fix(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
#     pass