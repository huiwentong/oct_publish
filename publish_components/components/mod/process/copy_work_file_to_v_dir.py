import traceback
import inspect
import time

def main(submit_data:dict, process_data:dict, parent_widget=None):
    """
复制预工作文件到版本文件夹
    """
    try:
        print('copy_work_file_to_v_dir!!!!!!')
        time.sleep(2)
    except:
        return traceback.format_exc()