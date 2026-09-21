# -*- coding: utf-8 -*-
import traceback
from oct.pipeline.task_context import TaskContext
from publish_core.message_utils.message import send_simple_message

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """发送消息给下游制作人员"""
    def get_downstream_users(tc, steps):
        users = []
        for _task in tc.entity.tasks:
            if _task.step.short_name.lower() not in steps:
                continue
            if not _task.versions():
                continue
            last_version = _task.latest_version_by_types(['Submit', "Publish"])

            if not last_version:
                continue
            users.append({"sg_dingtalk_id": last_version.user.sg_dingtalk_id})
        return users

    try:
        step_maps = {
                     "mod" : ["tex"]
                    }

        task_id = process_data["task_id"]
        task_context = TaskContext(task_id) or TaskContext.from_env()
        current_step_name = task_context.step.short_name.lower()
        downstream_step_names = step_maps.get(current_step_name, [])
        meg_to_downstream = process_data.get("meg_to_downstream")
        if downstream_step_names and meg_to_downstream:
            downstream_users = get_downstream_users(task_context, downstream_step_names)
            if downstream_users:
                comment = "上游环节提交了新的版本：\n"
                texts = []
                for desp, content in meg_to_downstream.items():
                    texts.append('{}: {}'.format(desp, content))
                comment += "\n({})".format("\n".join(texts))
                msg_data = {
                    'message': comment,
                    'type': process_data.get("publish_type"),
                    'vname': process_data.get("version_name"),
                    'tname': task_context.task_name,
                    'ename': task_context.entity_name,
                }
                for user_dict in downstream_users:
                    send_simple_message(msg_data, '来自发布者的提醒', user_dict)

    except Exception:
        return traceback.format_exc()
