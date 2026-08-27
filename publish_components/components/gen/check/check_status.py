# -*- coding: utf-8 -*-
import traceback
from publish_core.database.entity import SGEntity

def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
    检查资产、镜头、任务状态 是否 omt/hld
    """
    # 检查资产、镜头、任务状态 是否 omt/hld，如果是，需要 PC 改状态再 Publish

    try:
        disable_pub_status = ['omt', 'hld']
        task = SGEntity('Task', process_data['task_id'])
        task.flush()


        entity_status = task.entity.sg_status_list
        if entity_status in disable_pub_status:
            return u"{} {} 的状态为 {}，不能再提交新版本了。请找 PC 改状态".format(task.entity.type, task.entity.code, entity_status)

        task_status = task.sg_status_list
        if task_status in disable_pub_status:
            return u"任务 {} 的状态为 {}，不能再提交新版本了。请找 PC 改状态".format(task.content, task_status)

    except:
        return traceback.format_exc()


def fix(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    logger.info(process_data)