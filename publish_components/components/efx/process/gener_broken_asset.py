import os
import hou
import traceback
import subprocess
import shotgun_api3
from oct.pipeline.path_acs import lock_path, unlock_path, make_dirs
from publish_core.database.entity import FastSg, SGEntity
from oct.data.usd import step_pub_usds


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
生成破碎资产任务以及版本
    """
    try:
        def check_create_broken_asset(shotgun: shotgun_api3.Shotgun, asset_name, project_entity:SGEntity, shot_entity):

            filters = [
                ['code', 'is', asset_name],
                ['project', 'name_is', project_entity.code.upper()],
            ]
            ass = shotgun.find_one('Asset', filters, ['code'])

            if not ass:
                ori_asset_name = asset_name.split('_broken')[0]
                filters[0] = ['code', 'is', ori_asset_name]
                ori_ass = shotgun.find_one('Asset', filters, ['code'])
                seq_entity:SGEntity = shot_entity.sg_sequence
                asset_data = {
                    'sg_classify_code': '破碎资产',
                    'sg_asset_type': 'PROP',
                    'sg_list': 'prp',
                    'project': project_entity.tiny_raw(),
                    'sg_poly_hi_cnt': 0,
                    'parents': [ori_ass],
                    'task_template': {
                        'id': 51,
                        'type': 'TaskTemplate'
                    },
                    'sequences': [seq_entity.tiny_raw()],
                    'shots': [shot_entity.tin_raw()],
                    'code': asset_name,
                }
                ass = shotgun.create('Asset', asset_data)
            return ass

        def create_version(shotgun: shotgun_api3.Shotgun, ass_info, cache_file):

            ass_name = ass_info['code']
            filters = [
                ['entity', 'is', {'type': ass_info['type'], 'id': ass_info['id']}],
                ['content', 'is', 'model']
            ]
            task = shotgun.find_one('Task', filters, ['content', 'sg_last_version', 'project'])
            ver_filters = [
                ['sg_task', 'is', {'type': 'Task', 'id': task['id']}],
            ]
            vers = shotgun.find('Version', filters=ver_filters, fields=['code'],
                                order=[{'field_name': 'id', 'direction': 'desc'}])
            if not vers:
                ver_name = f'{ass_name}.mod.model.v001'
            else:
                if task['sg_last_version']:
                    ver_name = add_ver_name(task['sg_last_version']['name'])
                else:
                    lastver = vers[-1]
                    ver_name = add_ver_name(lastver['code'])

            ver_folder = f'I:/projects/{task["project"]["name"].lower()}/asset/prp/{ass_name}/mod/{ver_name}'
            print(ver_folder)
            if not os.path.exists(ver_folder):
                make_dirs(ver_folder)
            unlock_path(ver_folder, True)

            geo_file, pre_file = gen_maya_project_and_preview(cache_file, ver_folder, ver_name)
            mov_file = convert_preview(pre_file, ver_folder, ver_name)

            ver_data = {
                'code': ver_name,
                'project': task['project'],
                'sg_task': {'type': 'Task', 'id': task['id']},
                'description': '由特效镜头阶段发布工具自动发布的破碎资产版本',
                'entity': {'type': ass_info['type'], 'id': ass_info['id']},
                'sg_path_to_geometry': geo_file,
                'sg_path_to_movie': mov_file,
                'sg_path_to_v_folder': ver_folder,
                'sg_version_folder': None,
                'sg_version_type': 'Publish',
            }

            step_pub_usds.ModStepUsd(version_folder=ver_folder, task_id=task['id'])
            version = shotgun.create('Version', ver_data)
            shotgun.upload(entity_type='Version', entity_id=version['id'], path=mov_file,
                           field_name='sg_uploaded_movie')
            lock_path(ver_folder, True)

        def gen_maya_project_and_preview(usd_file, ver_folder, maya_name):
            maya_file = ver_folder + '/' + maya_name + '.ma'
            preview_file = ver_folder + '/preview/auto.png'
            pre_dir = ver_folder + '/preview'
            if not os.path.exists(pre_dir): os.makedirs(pre_dir)
            maya_script = os.path.dirname(__file__).replace('\\', '/') + '/generpreview.py'
            cmd = [
                r"C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe",
                maya_script,
                "--scene",
                maya_file,
                "--render_folder",
                preview_file,
                "--cache",
                usd_file,
            ]

            print(' '.join(cmd))
            subprocess.run(cmd, shell=True, check=True, env=get_utils_env())
            return maya_file, preview_file

        def add_ver_name(ver_name):
            vnum = ver_name.split('.')[-1]
            num = 'v' + str(int(vnum[1:]) + 1).zfill(3)
            v_all = ver_name.split('.')
            v_all[-1] = num
            return '.'.join(v_all)

        def convert_preview(v_dir_preview, out_dir, ver_name):
            convert_output = out_dir + f"/preview/{ver_name}.mov"
            convert_command = 'ffmpeg -framerate 30 -i {} -strict experimental -y -vcodec libx264 -pix_fmt yuv420p -g 30 -vprofile high -bf 0 -crf 23 -vf "scale=ceil(iw/2)*2:ceil(ih/2)*2" {}'.format(
                v_dir_preview, convert_output)
            print('************* --- convert_command is {}'.format(convert_command))
            import subprocess
            sp = subprocess.Popen(convert_command)
            sp.wait()
            print('old preview is:{}'.format(v_dir_preview))
            print('convert preview is :{}'.format(convert_output))
            return convert_output

        def get_utils_env():
            env = {
                "ADSK_CLM_WPAD_PROXY_CHECK": r"FALSE",
                "ALLUSERSPROFILE": r"C:\ProgramData",
                "APPDATA": r"C:\Users\huiwentong\AppData\Roaming",
                "CommonProgramFiles": r"C:\Program Files\Common Files",
                "CommonProgramFiles(x86)": r"C:\Program Files (x86)\Common Files",
                "CommonProgramW6432": r"C:\Program Files\Common Files",
                "ComSpec": r"C:\Windows\system32\cmd.exe",
                "DEADLINE_PATH": r"C:\Program Files\Thinkbox\Deadline10\bin",
                "DEFAULT_RENDERER": r"dl",
                "DELIGHT": r"C:\Program Files\3Delight",
                "DriverData": r"C:\Windows\System32\Drivers\DriverData",
                "HOMEDRIVE": r"C:",
                "HOMEPATH": r"\Users\huiwentong",
                "INTEL_DEV_REDIST": r"C:\Program Files (x86)\Common Files\Intel\Shared Libraries",
                "KATANA_RESOURCES": r"C:\Program Files\3Delight\3DelightForKatana",
                "LOCALAPPDATA": r"C:\Users\huiwentong\AppData\Local",
                "LOGONSERVER": r"\\WC",
                "MIC_LD_LIBRARY_PATH": r"C:\Program Files (x86)\Common Files\Intel\Shared Libraries\compiler\lib\mic",
                "NUMBER_OF_PROCESSORS": r"64",
                "OneDrive": r"C:\Users\Skyfree\OneDrive",
                "OS": r"Windows_NT",
                "Path": r"C:\Program Files (x86)\Common Files\Intel\Shared Libraries\redist\intel64\compiler;C:\Windows\system32;C:\Windows;C:\Windows\System32\Wbem;C:\Windows\System32\WindowsPowerShell\v1.0\;C:\Windows\System32\OpenSSH\;C:\Users\Skyfree\AppData\Local\Microsoft\WindowsApps;C:\Program Files\3Delight\bin;C:\Program Files (x86)\QuickTime\QTSystem\;C:\Program Files (x86)\NVIDIA Corporation\PhysX\Common;C:\Program Files\Microsoft VS Code\bin;C:\Program Files\Git\cmd;D:\prealStudio;C:\Program Files\Microsoft SQL Server\150\Tools\Binn\;C:\Program Files\Microsoft SQL Server\Client SDK\ODBC\170\Tools\Binn\;C:\Program Files\dotnet\;C:\Program Files (x86)\Windows Kits\10\Windows Performance Toolkit\;C:\Program Files\CMake\bin;C:\Program Files\Python310\Scripts\;C:\Program Files\Python310\;C:\opt\Scripts\rez;C:\opt\Scripts;C:\Users\huiwentong\AppData\Local\Microsoft\WindowsApps;;C:\Program Files\JetBrains\PyCharm 2025.1.2\bin;;C:\Users\huiwentong\.dotnet\tools",
                "PATHEXT": r".COM;.EXE;.BAT;.CMD;.VBS;.VBE;.JS;.JSE;.WSF;.WSH;.MSC;.PY;.PYW",
                "PROCESSOR_ARCHITECTURE": r"AMD64",
                "PROCESSOR_IDENTIFIER": r"Intel64 Family 6 Model 85 Stepping 7, GenuineIntel",
                "PROCESSOR_LEVEL": r"6",
                "PROCESSOR_REVISION": r"5507",
                "ProgramData": r"C:\ProgramData",
                "ProgramFiles": r"C:\Program Files",
                "ProgramFiles(x86)": r"C:\Program Files (x86)",
                "ProgramW6432": r"C:\Program Files",
                "PROMPT": r"$P$G",
                "PSModulePath": r"C:\Program Files\WindowsPowerShell\Modules;C:\Windows\system32\WindowsPowerShell\v1.0\Modules",
                "PUBLIC": r"C:\Users\Public",
                "PyCharm": r"C:\Program Files\JetBrains\PyCharm 2025.1.2\bin;",
                "REZ_CONFIG_FILE": r"\\192.168.15.15\pipeline\config\rezconfig.py",
                "SESSIONNAME": r"Console",
                "SystemDrive": r"C:",
                "SystemRoot": r"C:\Windows",
                "USERDNSDOMAIN": r"DS.COM",
                "USERDOMAIN": r"DS",
                "USERDOMAIN_ROAMINGPROFILE": r"DS",
                "USERNAME": r"huiwentong",
                "USERPROFILE": r"C:\Users\huiwentong",
                "windir": r"C:\Windows"
            }
            for k, v in env.items():
                env[k] = v.replace('huiwentong', os.environ['username'])
            return env


        v_comp_dir = process_data['version_dir'] + '/components'
        sg = FastSg().client
        task = SGEntity('Task', process_data['task_id'])
        for k,v in submit_data['components'].items():
            comp_path = v_comp_dir+f'/{k}'
            if not os.path.exists(comp_path):
                make_dirs(comp_path)
            comp_node:hou.SopNode = v['cache_node']
            comp_type = v['cache_type']
            if comp_type != '破碎缓存': continue
            broken_asset_name = comp_node.parm('broken_name').eval()

            project_name = task.project.code
            shot = task.entity

            logger.info('gener asset!!!')
            logger.info(broken_asset_name, project_name)
            ass = check_create_broken_asset(sg, broken_asset_name, project_name, shot)
            cache = comp_node.parm('lopoutput').eval()
            logger.info('gener version!!!!')
            create_version(sg, ass, cache)

    except:
        logger.error(traceback.format_exc())
        return traceback.format_exc()






