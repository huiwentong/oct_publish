import traceback
import os
import shutil
import traceback
import sys
import subprocess
from oct.pipeline.path_acs import lock_path, unlock_path, make_dirs
from publish_components.utils import images
from publish_core.database.entity import get_user, SGEntity
from publish_core.database.core import FastSg
from publish_components.utils.edit_utils import split_video, split_audio
from datetime import datetime
import shutil

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
创建Publish类型的发布文件
    """
    try:
        sg = FastSg().client
        vd = process_data['version_dir']
        vd_preview = vd + '/preview'
        if not os.path.exists(vd_preview):
            make_dirs(vd_preview)
        
        user = process_data.get("user") or get_user().tiny_raw()
        task_id = process_data.get("task_id")
        tc = SGEntity(entity_type='Task', entity_id=task_id)
        version_dir:str = process_data.get("version_dir")
        version_name = process_data.get("version_name")
        v_dir_preview:str = process_data.get("v_dir_preview")
        publish_mode = process_data.get("publish_type")
        comment = process_data.get("comment")
        v_num = process_data['version_num']
        edit_preview = 'Z:/TD/pipeline/resource/oct_publish/edt_preview.png'


        if sys.platform.startswith('win'):
            local_path = version_dir.replace('/', '\\') + '\\'
        else:
            local_path = version_dir + '/'


        entity_dict = {"id": tc.entity.id, "type": tc.entity.type}
        sg_task_dict = {"id": task_id, "type": "Task"}
        project_dict = {"id": tc.project.id, "type": tc.project.type}
        tag_entity = SGEntity('Tag', process_data.get("publish_tag_id"))
        d_version = {
            'project': project_dict,
            'entity': entity_dict,
            'sg_task': sg_task_dict,
            'code': version_name,
            'description': comment,
            'user': user,
            'sg_version_type': publish_mode,
            'tag_list': [tag_entity.name],
            'created_by': user,
            'sg_path_to_v_folder': version_dir,
            'sg_path_to_movie': v_dir_preview,
            'sg_version_folder': {
                'local_path': local_path,
                'name': version_name,
                'content_type': None,
                'link_type': 'local'
            }
        }
        v_info = sg.create('Version', d_version)

        sg.upload('Version', v_info['id'], edit_preview, "sg_uploaded_movie")


        # 进入镜头发布阶段！-----------------------------------------------
        mov = submit_data['mov_file']
        date_str = datetime.now().strftime("%Y%m%d")
        p_publish_v = f"P:/MK2/20_Publish/{tc.entity.code}/{date_str}_tool_pub"
        
        if not os.path.exists(p_publish_v):
            make_dirs(p_publish_v)
            make_dirs(p_publish_v+'/shot')
            make_dirs(p_publish_v+'/wav')

        logger.info('正在生成P盘视频……')
        split_video(mov, submit_data['clip_data'], f"P:/MK2/20_Publish/{tc.entity.code}/{date_str}_tool_pub/shot")
        logger.info('正在生成P盘音频……')
        split_audio(mov, submit_data['clip_data'], f"P:/MK2/20_Publish/{tc.entity.code}/{date_str}_tool_pub/wav")
        logger.info('正在将串场视频拷贝到P盘……')
        shutil.copy(mov, f"P:/MK2/20_Publish/{tc.entity.code}/{date_str}_tool_pub/{process_data['project_name']}_{tc.entity.code}.mov")
        shutil.copy(submit_data['edl_file'], f"P:/MK2/20_Publish/{tc.entity.code}/{date_str}_tool_pub")
        logger.info('P盘全部发布完毕！')

        for _clip in submit_data['clip_data']:
            shot_name = _clip['clip_name']
            s_filter = [
                ['project', 'is', project_dict],
                ['code', 'is', shot_name]
            ]
            shot = sg.find_one('Shot', s_filter, ['id'])

            st_filter = [
                ['project', 'is', project_dict],
                ['entity', 'is', shot],
                ['content', 'is', 'editing']
            ]
            task = sg.find_one('Task', st_filter, ['id'])


            
            s_v_name = version_name.replace(tc.entity.code, shot_name)
            s_v_dir = f'i:/projects/{tc.project.code}/shot/{tc.entity.code}/{shot_name}/edt/{s_v_name}'
            s_v_preview = s_v_dir + f'/preview/{s_v_name}.mov'
            source_preview = f"P:/MK2/20_Publish/{tc.entity.code}/{date_str}_tool_pub/shot/{shot_name}.mov"

            if not os.path.exists(s_v_dir):
                make_dirs(s_v_dir)

            unlock_path(s_v_dir, True)

            if not os.path.exists(s_v_dir+'/preview'):
                make_dirs(s_v_dir+'/preview')

            shutil.copy(source_preview, s_v_preview)
            lock_path(s_v_dir, True)


            if sys.platform.startswith('win'):
                local_path = s_v_dir.replace('/', '\\') + '\\'
            else:
                local_path = s_v_dir + '/'
            
            d_s_version = {
                'project': project_dict,
                'entity': shot,
                'sg_task': task,
                'code': s_v_name,
                'description': comment + '\n\n剪辑发布工具自动拆分发布',
                'user': user,
                'sg_version_type': publish_mode,
                'tag_list': [tag_entity.name],
                'created_by': user,
                'sg_path_to_v_folder': s_v_dir,
                'sg_path_to_movie': s_v_preview,
                'sg_version_folder': {
                    'local_path': local_path,
                    'name': s_v_name,
                    'content_type': None,
                    'link_type': 'local'
                }
            }
            logger.info(f"正在创建 Shot {shot_name} 的发布版本 {s_v_name}……")
            s_v_info = sg.create('Version', d_s_version)

            if os.path.exists(s_v_preview):
                convert_output = None
                if s_v_preview.endswith(".mov"):
                    convert_output = os.getenv("temp") + "/" + os.path.basename(s_v_preview)
                    convert_command = ("rez-env ffmpeg -- ffmpeg -i {}  "
                                        "-y -strict experimental -vcodec libx264 -vf \"pad=ceil(iw/2)*2:ceil(ih/2)*2\" "
                                        "-pix_fmt yuv420p -g 30 -vprofile high -bf 0 -crf 23 {}"
                                        "").format(s_v_preview, convert_output)
                    logger.info("create sg mov cmd: {}".format(convert_command))
                    logger.info("正在转码 Shot {} 的发布版本 {} 的预览视频……".format(shot_name, s_v_name))
                    sp = subprocess.Popen(convert_command, stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT, text=True)
                    stdout, _ = sp.communicate()
                    if sp.returncode != 0:
                        logger.error(
                            f"ffmpeg 转码失败 | cmd={convert_command} | rc={sp.returncode} | "
                            f"output={(stdout or '').strip()}"
                        )
                        raise RuntimeError("ffmpeg 转码失败")
                    logger.info(f"ffmpeg 转码完成: {convert_output}")
                logger.info(f"正在上传 Shot {shot_name} 的发布版本 {s_v_name} 的预览视频……")
                if convert_output and os.path.exists(convert_output):
                    sg.upload('Version', s_v_info['id'], convert_output, "sg_uploaded_movie")
                else:
                    sg.upload('Version', s_v_info['id'], s_v_preview, "sg_uploaded_movie")


            


        
    except:
        return traceback.format_exc()