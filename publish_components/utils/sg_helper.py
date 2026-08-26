# coding=utf-8

from oct.pipeline.shotgun.models import Task
from publish_core.database.entity import FastSg


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

def check_is_internal_rig(task_id):
    sg = FastSg().client
    artist_list = []
    task_e = sg.find('Task', [['id', 'is', task_id]], ['task_assignees'])
    if task_e:
        for e in task_e[0]['task_assignees']:
            if e['type'] == 'Group':
                grp_e = sg.find_one('Group', [['id', 'is', e['id']]], ['name', 'sg_login'])
                artist_list.append(grp_e['sg_login'])
            else:
                person_e = sg.find_one('HumanUser', [['id', 'is', e['id']]], ['name', 'login'])
                artist_list.append(person_e['login'])

    print(artist_list)
    if 'kekedou' in artist_list:
        return False
    else:
        return True