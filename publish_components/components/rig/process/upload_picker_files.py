import os
import shutil
import traceback
from oct.pipeline import path_acs
from oct.pipeline.task_context import TaskContext


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
上传 Picker 文件
    """

    try:
        task_id = process_data.get("task_id")
        tc = TaskContext(task_id) or TaskContext.from_env()
        asset_name = tc.entity_name
        upper_project_name = tc.project_name.upper()

        asset_picker_dir = "W:/projects/lib/Ani_lib/MG_picker" + '/' + upper_project_name + '/' + asset_name
        submit_picker_files = submit_data['submit_picker_files']
        for file in submit_picker_files:
            source = file.replace('\\', '/')
            file_name = os.path.basename(source)
            target = asset_picker_dir + '/' + str(file_name)
            logger.info("{} -> {}".format(source, target))
            if source == target:
                logger.info("源与目标一样，跳过")
                continue
            if not os.path.exists(source):
                return u"复制失败，文件不存在 {}".format(source)

            target_dir = os.path.dirname(target)
            if not os.path.exists(target_dir):
                path_acs.make_dirs(target_dir)
            shutil.copy2(source, target)

    except Exception:
        return traceback.format_exc()
