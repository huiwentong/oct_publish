import traceback
import os
from pprint import pprint
import time


def main(submit_data:dict, process_data:dict, parent_widget=None):
    """
用来检查发布根路径
    """
    try:
        pprint(process_data)
        print('check_publish_root!!!!!!')
        time.sleep(2)
        raise RuntimeError('test error')
    except:
        return traceback.format_exc()