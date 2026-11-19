# -*- coding: utf-8 -*-
import os
import shutil
import subprocess
import tempfile
import traceback


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    生成场次版本的预览 mov：选了就拷贝，没选就按镜头号顺序拼接各镜头拍屏
    """
    # 替代 gen/copy_preview_to_v_dir（空预览时它会去拿图片序列生成 mov 并失败）。
    # 拼接用 ffmpeg concat 直接拷贝码流，不重新编码，要求各镜头拍屏编码 / 分辨率一致（拍屏工具出的都一致）。
    # 不用 oct_maya 的 comp_videos：Dailies 可能在没有 Maya 环境的 cmd 模式下跑，组件顶部 import 会被提到脚本最前面。
    try:
        v_dir_preview = process_data['v_dir_preview']
        preview_paths = process_data.get('preview_paths') or []
        if preview_paths:
            shutil.copyfile(preview_paths[0], v_dir_preview)
        else:
            linked_task_info = process_data.get('linked_task_info') or {}
            if not linked_task_info:
                return u'没有选择场次预览，也没有可拼接的镜头拍屏'
            movs = [linked_task_info[shot]['preview'] for shot in sorted(linked_task_info)]
            fd, list_file = tempfile.mkstemp(suffix='.txt', prefix='seq_lay_concat_')
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(''.join("file '{0}'\n".format(m.replace('\\', '/')) for m in movs))
            cmd = 'rez-env ffmpeg -- ffmpeg -y -f concat -safe 0 -i "{0}" -c copy "{1}"'.format(list_file, v_dir_preview)
            logger.info(cmd)
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    universal_newlines=True, encoding='utf-8', errors='replace')
            os.remove(list_file)
            if result.returncode != 0 or not os.path.isfile(v_dir_preview):
                return u'拼接场次预览失败:\n{0}'.format(result.stdout[-2000:])
        logger.info(u'v_dir_preview: {0}'.format(v_dir_preview))
    except:
        return traceback.format_exc()
