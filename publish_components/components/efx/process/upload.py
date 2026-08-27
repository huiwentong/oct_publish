# -*- coding: utf-8 -*-
import os
import traceback
import re
from oct.pipeline.shotgun.const import ComponentType
import subprocess
from oct.pipeline.shotgun.models import Task
from oct.utils.path import Path
from publish_components.utils import images
from pprint import  pprint





def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
在 Shotgun 上创建主版本，并保存相应文件。
    """
    try:

        description = process_data['comment']
        # TODO: 现在publish工具还没有autodescription的功能，看后续是否有必要要加上
        # auto_description = self.dialog.w_publish.plainTextEdit_auto_description.toPlainText()
        # if auto_description:
        #     self.dialog.description += '\n{ ' + auto_description + ' }'


        task = Task.get(id=process_data['task_id'])

        component = task.get_or_create_component('main', type=ComponentType.TYPE_3D)
        rig_file = ''
        if process_data['dcc'] == 'Houdini':
            rig_file = process_data['geo_file']
        else:
            pass
        version_data = {
            'code': process_data['version_name'],
            'description': description,
            'sg_version_type': process_data['publish_type'],
            'tags': [process_data['tag_entity']],
            'user': process_data['user'],
            'sg_task': {'type': 'Task', 'id': task.id},
            'sg_version_number': process_data['version_num'][1:],
            'sg_exported_path': process_data['version_dir'],
            'sg_path_to_movie': process_data['v_dir_preview'],
            'sg_path_to_geometry': rig_file,
        }
        res_x, res_y, duration = images.get_info_by_ffprobe(
            process_data['v_dir_preview']
        )

        if duration:
            version_data['frame_count'] = duration
            process_data['preview_duration'] = duration

        version = component.next_version(
            create=True,
            data=version_data
        )
        c_version = component.next_component_version(
            create=True,
            data={
                'code': process_data['version_name'],
                'sg_exported_path': str(Path(process_data['version_dir']))
            }
        )
        version.add_component_version(c_version)

        convert_output = os.getenv("temp") + "/" + os.path.basename(process_data['v_dir_preview'])
        convert_command = 'ffmpeg -i {} -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" -strict experimental -y -vcodec libx264 -pix_fmt yuv420p -g 30 -vprofile high -bf 0 -crf 23 {}'.format(process_data['v_dir_preview'], convert_output)

        sp = subprocess.Popen(convert_command)
        sp.wait()
        logger.info(convert_command)
        username = os.getenv('USERNAME')
        convert_output = re.sub(r'Users\\.*\\A', r'Users\\' + username + r'\\A', convert_output)
        logger.info(convert_output)

        version.upload(path=convert_output)
        process_data['v_info'] = version.to_dict()

    except Exception:
        traceback.print_exc()
        return traceback.format_exc()


