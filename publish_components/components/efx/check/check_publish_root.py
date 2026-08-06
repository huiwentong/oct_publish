import traceback
from pprint import pprint
import os
from publish_core.database.entity import SGEntity
from oct.pipeline.path_acs import make_dirs

def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
检查版本目录文件夹是否存在
    """
    try:
        task = SGEntity('Task', process_data['task_id'])

        if task.entity.type == "Shot":
            link = task.entity.sg_sequence.code
        else:
            link = 'efx'

        path_schema = "I:/projects/{pro}/{entity_type}/{entity_link}/{entity_name}/efx".format(
            pro=task.project.name,
            entity_type=task.entity.type,
            entity_name=task.entity.code,
            entity_link=link,
        )
        process_data['v_dir'] = path_schema + f'/{task.entity.code}.efx.{task.content}.v{str(process_data["version_num"]).zfill(3)}'

        if not os.path.isdir(path_schema):
            try:

                make_dirs(path_schema)
            except Exception:
                return u'版本的目录文件夹创建失败!:\n' + path_schema + traceback.format_exc()

    except:
        return traceback.format_exc()