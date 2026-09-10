# -*- coding: utf-8 -*-
import os
import traceback

import maya.utils as utils

from publish_components.utils.maya_utils import take_each_object_snapshot


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    为每个资产创建缩略图
    """
    # 通过拍屏的方式，为每个拆分出来的资产创建一张缩略图，
    # 农场端发布子资产时会把它上传成 SG 版本的封面
    try:
        version_dir = process_data["version_dir"]
        gen_asset_data = process_data["gen_asset_data"]

        snapshot_dir = os.path.join(version_dir, 'snapshot')
        if not os.path.exists(snapshot_dir):
            os.makedirs(snapshot_dir)
            logger.info(u"创建缩略图目录: {0}".format(snapshot_dir))

        group_list = [i['longname'] for i in gen_asset_data.values()]

        # 已存在的缩略图先删掉，避免拍屏失败时留下上一版的图
        for longname in group_list:
            short_name = longname.split('|')[-1]
            thumb_file = os.path.join(snapshot_dir, '{0}.png'.format(short_name))
            if os.path.exists(thumb_file):
                os.remove(thumb_file)

        # 拍屏要切视图、改相机，必须在主线程执行
        utils.executeInMainThreadWithResult(
            lambda: take_each_object_snapshot.main(group_list=group_list,
                                                   output_dir=snapshot_dir))

        logger.info(u"已为 {0} 个资产生成缩略图".format(len(group_list)))

    except:
        return traceback.format_exc()
