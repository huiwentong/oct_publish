import os
import shutil
import traceback
import sys
import subprocess
from oct.pipeline.path_acs import lock_path, unlock_path, make_dirs
from publish_components.utils import images
from publish_core.database.entity import get_user, SGEntity
from publish_core.database.core import FastSg

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
创建Daily类型的发布文件
    """
    try:
        # 先发布工程daily

        if process_data.get("publish_type") == "Dailies":
            sg = FastSg().client
            projectedit = process_data.get("project_name", "").lower()
            edit_preview = 'Z:/TD/pipeline/resource/oct_publish/edt_preview.png'
            seq_mov = process_data['preview_paths'][0]
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
            }
            v_info = sg.create('Version', d_version)
            sg.upload('Version', v_info['id'], edit_preview, "sg_uploaded_movie")


            #  ---------------------------------------------------------------------------------------------------
            # 创建edit version
            edit_task_filter = [
                ['project', 'name_is', projectedit],
                ['content', 'is', 'editing'],
                ['entity', 'name_is', tc.entity.code]
            ]
            task:dict = sg.find_one('Task', edit_task_filter, ['id'])

            tc = SGEntity(entity_type='Task', entity_id=task['id'])
            entity_dict = {"id": tc.entity.id, "type": tc.entity.type}
            sg_task_dict = {"id": tc.id, "type": "Task"}
            project_dict = {"id": tc.project.id, "type": tc.project.type}


            if sys.platform.startswith('win'):
                local_path = version_dir.replace('/', '\\') + '\\'
            else:
                local_path = version_dir + '/'

            shutil.copy(seq_mov, process_data.get("v_dir_preview"))

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

            res_x, res_y, duration = images.get_info_by_ffprobe(v_dir_preview)

            if duration:
                d_version['frame_count'] = duration
                process_data["preview_duration"] = duration


            
            v_info = sg.create('Version', d_version)
            # 下游关联组件使用本次创建的确切 ID，禁止用 latest 反查。
            process_data['sg_version'] = {'type': 'Version', 'id': v_info['id']}

            ############################################# Uploaded Version Movie ###########################################
            if os.path.exists(v_dir_preview):
                convert_output = None
                if v_dir_preview.endswith(".mov"):
                    convert_output = os.getenv("temp") + "/" + os.path.basename(v_dir_preview)
                    convert_command = ("rez-env ffmpeg -- ffmpeg -i {}  "
                                        "-y -strict experimental -vcodec libx264 -vf \"pad=ceil(iw/2)*2:ceil(ih/2)*2\" "
                                        "-pix_fmt yuv420p -g 30 -vprofile high -bf 0 -crf 23 {}"
                                        "").format(v_dir_preview, convert_output)
                    logger.info("create sg mov cmd: {}".format(convert_command))
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

                if convert_output and os.path.exists(convert_output):
                    sg.upload('Version', v_info['id'], convert_output, "sg_uploaded_movie")
                else:
                    sg.upload('Version', v_info['id'], v_dir_preview, "sg_uploaded_movie")




    except:
        return traceback.format_exc()