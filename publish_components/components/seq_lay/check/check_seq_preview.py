# -*- coding: utf-8 -*-
import os
import traceback


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    检查场次预览：Dailies 必须选串屏 mov；Publish 可以不选，由各镜头拍屏自动拼接
    """
    # 替代 gen/check_selected_preview（它遇到空预览直接报错）。
    # 选了预览时只接受一个 mov，直接作为场次版本的预览。
    try:
        preview_paths = process_data.get('preview_paths') or []
        if preview_paths:
            if len(preview_paths) != 1 or not str(preview_paths[0]).lower().endswith('.mov'):
                return u'场次预览只接受一个 mov 文件'
            if not os.path.isfile(preview_paths[0]):
                return u'找不到预览文件: {0}'.format(preview_paths[0])
        elif process_data.get('publish_type') == 'Dailies':
            return u'Dailies 需要选择场次串屏 mov'
        else:
            logger.info(u'没有选择场次预览，发布时拼接各镜头拍屏')
    except:
        return traceback.format_exc()
