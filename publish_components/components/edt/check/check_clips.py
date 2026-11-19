
import traceback
import os
from publish_core.database.entity import SGEntity
from pprint import pprint
import re

def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
检查所有剪辑数据
    """
    try:
        data = submit_data['clip_data']
        tc = SGEntity('Task', process_data['task_id'])
        seq = tc.entity
        names = []
        for _clip in data:
            if _clip['clip_name'] in names:
                return f"剪辑名称重复：{_clip['clip_name']}"
            if not re.search(r'^[a-z]\d{2}(?:[a-z])?\d{4}$', _clip['clip_name']):
                return f"剪辑命名: {_clip['clip_name']} 不符合规范！"
            if not _clip['clip_name'].startswith(seq.code):
                return f"剪辑名称: {_clip['clip_name']} 没有以当前场次的标准名: {seq.code} 进行命名"
            
            names.append(_clip['clip_name'])




    except:
        return traceback.format_exc()




def fix(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    pass

