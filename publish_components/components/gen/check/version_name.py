# -*- coding: utf-8 -*-
import traceback
from oct.pipeline.path_acs import old_get_path
from publish_core.database.entity import SGEntity

def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
    检查版本(Version)的命名是否规范。
    """
    try:
        task_id = process_data['task_id']
        form_widget = process_data.get("widget")
        task = SGEntity('Task', task_id)
        if task.entity.type not in ['Asset', 'Shot', 'Sequence']:
            return u'无效的 entity type: {}'.format(task.entity.type)

        version_key = form_widget._version_name_label.text()
        version_num = form_widget._version_edit.text()
        version_name = version_key + version_num
        project_name = task.project.name
        entity_name = task.entity.code

        old_get_path(mount_point='work', show_name=project_name, entity_type="Task", id=task_id)
        work_root = old_get_path(mount_point='work', show_name=project_name, entity_type="Task", id=task_id)
        render_root = old_get_path(mount_point='output', show_name=project_name, entity_type="Task", id=task_id)
        publish_root = old_get_path(mount_point='publish', show_name=project_name, entity_type="Task", id=task_id)

        version_dir = publish_root + '/' + version_name
        version_dir_no_num = publish_root + '/' + version_key
        v_dir_preview = version_dir + '/preview/' + version_name + '.mov'
        v_dir_gpu = version_dir + '/gpu'
        v_dir_abc = version_dir + '/alembic'
        v_dir_usd = version_dir + '/usd'
        v_dir_ad = version_dir + '/assembly_definition/' + entity_name + '.ma'
        v_dir_shot_json = version_dir + '/shot_assets.json'
        v_dir_imgs = version_dir + '/sourceimages'
        v_dir_srcs = version_dir + '/sourcefiles'
        v_dir_klf = ""
        if task.entity.type == 'Asset':
            v_dir_ma_file = version_dir + '/' + entity_name + '.ma'
            v_dir_mb_file = version_dir + '/' + entity_name + '.mb'
            if task.entity.sg_asset_type == 'EFX':
                v_dir_klf = version_dir + '/klf/' + entity_name + '.klf'
        else:
            v_dir_ma_file = version_dir + '/' + version_name + '.ma'
            v_dir_mb_file = version_dir + '/' + version_name + '.mb'
        version_dir_data = {"version_key": version_key,
                            "version_num": version_num,
                            "version_name": version_name,
                            "work_root": work_root,
                            "render_root": render_root,
                            "publish_root": publish_root,
                            "version_dir": version_dir,
                            "version_dir_no_num": version_dir_no_num,
                            "v_dir_preview": v_dir_preview,
                            "v_dir_gpu": v_dir_gpu,
                            "v_dir_abc": v_dir_abc,
                            "v_dir_usd": v_dir_usd,
                            "v_dir_ad": v_dir_ad,
                            "v_dir_shot_json": v_dir_shot_json,
                            "v_dir_imgs": v_dir_imgs,
                            "v_dir_srcs": v_dir_srcs,
                            "v_dir_ma_file": v_dir_ma_file,
                            "v_dir_mb_file": v_dir_mb_file,
                            "v_dir_klf": v_dir_klf,
                            "project_name": project_name}

        process_data.update(version_dir_data)
        logger.info("version_dir_data: {}".format(version_dir_data))

    except:
        return traceback.format_exc()


