# -*- coding: utf-8 -*-
import glob
import os
import re
import shutil
import traceback
import maya.utils as utils
from publish_components.utils.maya_utils import asb_build

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """拷贝场景 file/aiImage 贴图，展开 UDIM 和帧序列并拒绝同名覆盖"""
    try:
        patterns = utils.executeInMainThreadWithResult(asb_build.scene_texture_paths)
        target_dir = process_data['v_dir_imgs']
        copy_plan = {}
        for pattern in patterns:
            parts = re.split(r'(<UDIM>|<f>|<frame>|#+)', pattern, flags=re.IGNORECASE)
            expanded = ''.join('*' if re.fullmatch(r'<UDIM>|<f>|<frame>|#+', part, re.IGNORECASE)
                               else glob.escape(part) for part in parts)
            sources = [p for p in glob.glob(expanded) if os.path.isfile(p)]
            if not sources:
                raise RuntimeError('贴图文件不存在: ' + pattern)
            for source in sources:
                target = os.path.join(target_dir, os.path.basename(source))
                key = os.path.normcase(target)
                previous = copy_plan.get(key)
                if previous and os.path.normcase(os.path.abspath(previous[0])) != os.path.normcase(os.path.abspath(source)):
                    raise RuntimeError('不同贴图具有相同文件名: {0} / {1}'.format(previous[0], source))
                copy_plan[key] = (source, target)
        os.makedirs(target_dir, exist_ok=True)
        for source, target in copy_plan.values():
            if os.path.normcase(os.path.abspath(source)) != os.path.normcase(os.path.abspath(target)):
                shutil.copyfile(source, target)
        logger.info('已拷贝 {0} 张 ASB 场景贴图'.format(len(copy_plan)))
    except Exception:
        return traceback.format_exc()
