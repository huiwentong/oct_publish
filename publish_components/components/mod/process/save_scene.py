import traceback
import inspect
import time

def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
保存场景
    """
    try:
        print('test!!!!!!')
        time.sleep(2)
    except:
        return traceback.format_exc()