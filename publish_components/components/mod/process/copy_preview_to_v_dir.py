import traceback
import inspect
import time

def main(submit_data:dict, process_data:dict, parent_widget=None):
    """
复制预览图到版本文件夹
    """
    try:
        print('copy_preview_to_v_dir!!!!!!')
        time.sleep(2)
    except:
        return traceback.format_exc()