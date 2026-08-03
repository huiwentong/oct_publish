import traceback
import os
from pprint import pprint
import time


def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
    这是一个用来检查dcc是否有rv的检查项
    """
    try:
        print('check dcc!!!!!!')
        time.sleep(2)
    except:
        return traceback.format_exc()



