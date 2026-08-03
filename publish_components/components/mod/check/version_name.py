import traceback
import sys
import datetime


def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
   检查版本名称！

    """
    try:
        print('version name!!!!!!')
    except:
        return traceback.format_exc()