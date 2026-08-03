import traceback
import os
from pprint import pprint
import time


def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
检查版本名称的合法性
    """
    try:
        print('version_name_match !!!!!')
        time.sleep(2)
    except:
        return traceback.format_exc()