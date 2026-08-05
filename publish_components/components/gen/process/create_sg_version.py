# -*- coding: utf-8 -*-
import os
import sys
import time
import traceback
import subprocess
from tk_oct_publish.proc import images
from oct.pipeline.task_context import TaskContext
from publish_core.database.entity import get_user, SGEntity

def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
    在 Shotgun 上创建版本，添加当日Daily
    """

    try:
        user = get_user().tiny_raw()
        tc = TaskContext(process_data.get("task_id"))
        version_dir = process_data.get("version_dir")
        version_name = process_data.get("version_name")
        v_dir_preview = process_data.get("v_dir_preview")
        publish_mode = process_data.get("publish_type")
        comment = process_data.get("comment")
        auto_comment = process_data.get("auto_comment")
        if auto_comment:
            comment += '\n{ ' + auto_comment + ' }'

        if sys.platform.startswith('win'):
            local_path = version_dir.replace('/', '\\') + '\\'
        else:
            local_path = version_dir + '/'

        ############################################# Create SG Version ################################################
        project_dict = tc.project.to_dict()
        tag_entity = SGEntity('Tag', process_data.get("publish_tag_id"))
        d_version = {
            'project': project_dict,
            'entity': tc.entity.to_dict(),
            'sg_task': tc.task.to_dict(),
            'code': version_name,
            'description': comment,
            'user': user,
            'sg_version_type': publish_mode,
            'tag_list': [tag_entity.name],
            'created_by': user,
            'sg_path_to_v_folder': process_data.get("process_data"),
            'sg_path_to_movie': v_dir_preview,
            'sg_version_folder': {
                'local_path': local_path,
                'name': process_data.get("version_name"),
                'content_type': None,
                'link_type': 'local'
            }
        }
        res_x, res_y, duration = images.get_info_by_ffprobe(v_dir_preview)

        if duration:
            d_version['frame_count'] = duration
            process_data["preview_duration"] = duration

        if publish_mode == "Publish":
            d_version['sg_path_to_geometry'] = process_data.get("v_dir_ma_file") or process_data.get("v_dir_katana")

        sg = tc.task.sg_client()
        v_info = sg.create('Version', d_version)

        ############################################# Uploaded Version Movie ###########################################
        if os.path.exists(v_dir_preview):
            convert_output = None
            if v_dir_preview.endswith(".mov") and tc.entity_type == "Shot":
                convert_output = os.getenv("temp") + "/" + os.path.basename(v_dir_preview)
                convert_command = ("rez-env ffmpeg -- ffmpeg -i {}  "
                                   "-y -strict experimental -vcodec libx264 -vf \"pad=ceil(iw/2)*2:ceil(ih/2)*2\" "
                                   "-pix_fmt yuv420p -g 30 -vprofile high -bf 0 -crf 23 {}"
                                   "").format(v_dir_preview, convert_output)
                logger.info("create sg mov cmd: {}".format(convert_command))
                sp = subprocess.Popen(convert_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                      universal_newlines=True)
                stdout, stderr = sp.communicate()
                print(stderr)

            if convert_output and os.path.exists(convert_output):
                sg.upload('Version', v_info['id'], convert_output, "sg_uploaded_movie")
            else:
                sg.upload('Version', v_info['id'], v_dir_preview, "sg_uploaded_movie")
        else:
            logger.info('no preview file: {}'.format(v_dir_preview))

        if tc.task_name == 'tex_view':
            return ''

        ############################################# Connection Playlist###############################################

        cur_time = time.gmtime()
        time_str = time.strftime("%Y%m%d", cur_time)
        code_name = '_'.join([tc.project_name.upper(), 'Dailies', time_str])

        filters = [['project', 'is', project_dict], ['code', 'is', code_name]]
        if not sg.find_one('Playlist', filters):
            data = {}
            data['project'] = project_dict
            data['code'] = code_name
            sg.create('Playlist', data)

        playlist = sg.find_one('Playlist', filters, ['id'])

        conn_data = {'playlist': {'type': 'Playlist', 'id': playlist['id']},
                     'version': {'type': 'Version', 'id': v_info['id']}}

        sg.create('PlaylistVersionConnection', conn_data)

    except:
        return traceback.format_exc()


