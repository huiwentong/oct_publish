import traceback
import os
import re
import hou
import oct_hou
from publish_core.database.entity import SGEntity

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
检查工程文件是否存在,检查工程文件名是否合规
    """
    try:
        task = SGEntity('Task', process_data['task_id'])
        step_name = task.step.short_name
        file = hou.hipFile.path()
        if not os.path.exists(file):
            return '当前工程文件还未保存，请先保存再执行下一步'
        taskinfo = oct_hou.TC['task']
        basename = hou.hipFile.basename()
        hipfile = f"{taskinfo['entity']['name']}.{step_name}.{taskinfo['content']}." + 'v....hip'

        if not re.match(hipfile, basename):
            return '当前工程命名不规范，请联系TD检查问题'
    except Exception:
        return traceback.format_exc()


