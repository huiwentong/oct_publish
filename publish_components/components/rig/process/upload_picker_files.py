import os
import shutil
import traceback
from oct.pipeline import path_acs
from oct.pipeline.task_context import TaskContext


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
上传 Picker 文件
    """
    # def _copy_rename(source, target):
    #     try:
    #         if not os.path.exists(source):
    #             logger.warning(f"错误：源文件不存在 - {source}")
    #             return False
    #
    #         if os.path.exists(target):
    #             logger.info(f"目标文件已存在，跳过 - {target}")
    #             return True
    #
    #         else:
    #             destination_dir = os.path.dirname(target)
    #             if not os.path.exists(destination_dir):
    #                 path_acs.make_dirs(destination_dir)
    #             shutil.copy2(source, target)
    #             logger.info(f"复制完成: {0} -> {1}".format(source, target))
    #             return True
    #
    #     except Exception as e:
    #         logger.error('复制失败: {}'.format(str(e)))
    #         return False

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

            destination_dir = os.path.dirname(target)
            if not os.path.exists(destination_dir):
                path_acs.make_dirs(destination_dir)
            shutil.copy2(source, target)







        # task_id = process_data.get("task_id")
        # tc = TaskContext(task_id) or TaskContext.from_env()
        # asset_name = tc.entity_name
        # picker_file_name = "{}.mgpkr".format(asset_name)
        #
        # file_name_list = ['Body_PkrImage.bmp', 'cloth.jpg', 'face.jpg', 'hair.jpg', picker_file_name]
        # default_picker_dir = "W:/projects/lib/Ani_lib/MG_picker/MK2/default_template"
        #
        #
        # submit_picker_files = submit_data.get("submit_picker_files", [])
        # if submit_picker_files:
        #     source_picker_file_list = submit_picker_files
        #     for file_name in file_name_list:
        #         # 补齐未上传的文件
        #         if file_name not in [os.path.basename(p) for p in source_picker_file_list]:
        #             source_picker_file_list.append(default_picker_dir + '/{}'.format(file_name))
        # else:
        #     source_picker_file_list = [default_picker_dir + '/{}'.format(f) for f in file_name_list]
        #
        # picker_file_list = process_data['picker_file_list']
        #
        # msg = ''
        # for source, target in zip(source_picker_file_list, picker_file_list):
        #     done = _copy_rename(source, target)
        #     if not done:
        #         msg += '复制失败: {} -> {},  '.format(source, target)
        #
        #     if msg:
        #         return msg

    except Exception:
        return traceback.format_exc()