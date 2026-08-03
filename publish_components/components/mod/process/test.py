import traceback
from glob import glob
import time


def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
测试用
    """
    try:
        print('test!!!!!!')
        time.sleep(1)
    except:
        return traceback.format_exc()