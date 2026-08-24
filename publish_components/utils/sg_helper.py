# coding=utf-8

from oct.pipeline.shotgun.models import Task


def is_rig_task_omit(task_id):
    """
    判断任务是否为弃用任务。如果任务的绑定状态为弃用，则返回True，否则返回False
    Args:
        task_id: int, the id of the task
    """
    if not isinstance(task_id, int):
        task_id = int(task_id)

    sg_task = Task.get(id=task_id)
    rig_task_status = None

    for t in sg_task.entity.tasks:
        if t.content == 'rigging':
            rig_task_status = t.sg_status_list
            break

    if not rig_task_status or rig_task_status == 'omt':
        return True
