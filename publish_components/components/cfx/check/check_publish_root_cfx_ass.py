
import traceback
import os
from oct.pipeline.shotgun.models import Task
from publish_core.database.entity import SGEntity
from oct.pipeline.path_acs import make_dirs


def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
检查版本目录文件夹是否存在
    """
    try:
        type_map = {
            'CH': 'chr',
            'PROP': 'prp',
        }
        step_map = {
            'Cloth': 'clo',
            'cfx': 'cfx',
            'CFX': 'cfx',
            'Fur': 'fur'
        }

        def run_fix(task: SGEntity):
            if task.entity.type == "Asset":
                link = type_map[task.entity.sg_asset_type]
            else:
                link = task.entity.sg_sequence.code
            path_schema = "I:/projects/{pro}/{entity_type}/{entity_link}/{entity_name}/{step_name}".format(
                pro=task.project.name.lower(),
                entity_type=task.entity.type.lower(),
                entity_name=task.entity.code,
                entity_link=link,
                step_name=step_map[task.step.code]
            )
            logger.info('************/ create path! {}'.format(path_schema))
            make_dirs(path_schema)

        task = SGEntity('Task', process_data['task_id'])

        if task.entity.type == "Asset":
            link = type_map[task.entity.sg_asset_type]
        else:
            link = task.entity.sg_sequence.code

        path_schema = "I:/projects/{pro}/{entity_type}/{entity_link}/{entity_name}/{step_name}".format(
            pro=task.project.name.lower(),
            entity_type=task.entity.type.lower(),
            entity_name=task.entity.code,
            entity_link=link,
            step_name=step_map[task.step.short_name]
        )
        logger.info(path_schema)
        if not os.path.isdir(path_schema):
            run_fix(task)
    except:
        return traceback.format_exc()






