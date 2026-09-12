# -*- coding: utf-8 -*-
import os
import shutil
import traceback

import maya.cmds as cmds
import maya.utils as utils
from qtpy import QtCore, QtWidgets

from publish_components.utils.texture_files import (TOKEN_PATTERN, TEXTURE_NODE_ATTRS, TextureFileResolver,
                                                    add_suffix, assign_collision_suffixes,
                                                    is_under_dir, need_copy, norm_path,
                                                    resolve_texture_pattern, set_texture_path)


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    检查贴图是否在当前工作目录下
    """
    # 场景里所有 file / aiImage 节点引用的贴图，必须放在当前工作文件所在目录下
    # （一般是 .../mod/maya/sourceimages），并且文件必须存在。
    # 拆分发布在 Deadline 端打开 source.ma 时不会设置 Maya 工程，相对路径解析不到，
    # 工程外的绝对路径又依赖 Deadline 机器能访问到，所以要求贴图都放在工作目录下，
    # 并且写成绝对路径。
    # 思路参考 oct_maya.tools.pipe.oct_save_as 的 copy_local_files。
    #
    # 检查结果写入 process_data['work_dir_textures']，供 fix() 拷贝和替换路径：
    #   outside: 工作目录外，需要拷贝  [{'node_attr', 'raw_path', 'pattern', 'files', 'dest_dir'}, ...]
    #   relative: 文件在工作目录下但写的是相对路径，只需改成绝对路径，格式同上
    #   missing: 找不到文件  [(node_attr, raw_path), ...]
    try:
        work_file = (submit_data.get("ma_file") or '').replace('\\', '/')
        if not work_file:
            return u"没有指定工作文件，无法确定工作目录"
        work_dir = norm_path(os.path.dirname(work_file))
        tex_dir = work_dir + '/sourceimages'

        def get_dest_dir(pattern):
            # 源文件的父文件夹名不是 sourceimages 时，在 sourceimages 下保留这一级文件夹名，
            # 避免不同来源的同名贴图互相覆盖，与 oct_save_as 的做法一致
            parent_name = os.path.basename(os.path.dirname(pattern))
            if parent_name.lower() == 'sourceimages':
                return tex_dir
            return tex_dir + '/' + parent_name

        # 遍历贴图节点要读 Maya 属性，收进 collect() 调度回主线程
        def collect():
            resolver = TextureFileResolver()
            outside, relative, inside, missing = [], [], [], []

            for node_type, attr_name in TEXTURE_NODE_ATTRS.items():
                try:
                    nodes = cmds.ls(type=node_type) or []
                except RuntimeError:
                    # 对应插件（如 mtoa）没加载时节点类型不存在
                    nodes = []

                for node in nodes:
                    node_attr = node + '.' + attr_name
                    raw_path, pattern = resolve_texture_pattern(node, attr_name)
                    if not pattern:
                        continue

                    files = resolver.find_files(pattern)
                    if not files:
                        missing.append((node_attr, raw_path))
                        continue

                    info = {'node_attr': node_attr,
                            'raw_path': raw_path,
                            'pattern': pattern,
                            'files': files}
                    if not is_under_dir(pattern, work_dir):
                        info['dest_dir'] = get_dest_dir(pattern)
                        outside.append(info)
                    elif not os.path.isabs(raw_path.replace('\\', '/')):
                        # 文件已经在工作目录下，不用拷贝，原地改成绝对路径
                        info['dest_dir'] = os.path.dirname(pattern)
                        relative.append(info)
                    else:
                        # 已在工作目录里的绝对路径不报错，但自动修复外部贴图时必须把它
                        # 当成保留项，避免同名外部贴图覆盖它。
                        info['dest_dir'] = os.path.dirname(pattern)
                        inside.append(info)

            return outside, relative, inside, missing

        outside, relative, inside, missing = utils.executeInMainThreadWithResult(collect)
        process_data['work_dir_textures'] = {'outside': outside,
                                             'relative': relative,
                                             'inside': inside,
                                             'missing': missing}

        msg = ''
        if outside:
            msg += u"以下 {0} 个贴图节点的贴图不在工作目录 {1} 下，可用自动修复拷贝到 {2}:\n".format(
                len(outside), work_dir, tex_dir)
            for info in outside:
                msg += u"{0}: {1}\n".format(info['node_attr'], info['raw_path'])
            msg += '\n'

        if relative:
            msg += u"以下 {0} 个贴图节点写的是相对路径，Deadline 端解析不到，可用自动修复改为绝对路径:\n".format(
                len(relative))
            for info in relative:
                msg += u"{0}: {1}\n".format(info['node_attr'], info['raw_path'])
            msg += '\n'

        if missing:
            msg += u"以下 {0} 个贴图节点的贴图文件不存在，无法自动修复，请手动处理:\n".format(len(missing))
            for node_attr, raw_path in missing:
                msg += u"{0}: {1}\n".format(node_attr, raw_path)

        if msg:
            return msg

    except Exception:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    把工作目录外的贴图拷贝到工作目录的 sourceimages 下，并把节点路径替换为拷贝后的绝对路径
    """
    try:
        result = process_data.get('work_dir_textures') or {}
        outside = result.get('outside', [])
        relative = result.get('relative', [])
        inside = result.get('inside', [])
        missing = result.get('missing', [])

        # 没有可修的项时不能裸 return：CLI 模式下组件被平铺进同一个脚本，
        # 裸 return 会把整条流程中止
        if not outside and not relative and missing:
            return u"只有文件不存在的贴图，无法自动修复"

        # 先按实际目标文件名检查冲突。工作目录内已有的贴图只作为保留项，
        # 冲突时给外部贴图统一加内容哈希后缀，不能覆盖已有文件。
        conflict_count = assign_collision_suffixes(outside, reserved_groups=relative + inside)
        if conflict_count:
            logger.warning(u"AUTO FIX: 检测到目标文件名冲突，已给 {0} 组贴图增加哈希后缀".format(
                conflict_count))

        # 先按源文件去重，同一张贴图被多个节点引用时只拷一次
        copy_jobs = []
        seen = set()
        for info in outside:
            for src_file in info['files']:
                src_name = os.path.basename(src_file)
                suffix = info.get('suffix', '')
                dst_name = add_suffix(src_name, suffix) if suffix else src_name
                dst_file = info['dest_dir'] + '/' + dst_name
                key = src_file.lower()
                if key in seen:
                    continue
                seen.add(key)
                copy_jobs.append((src_file, dst_file))

        copied = 0
        if copy_jobs:
            # fix 由按钮点击直接调用，在主线程，可以弹进度条；CLI 下没有父窗口就不弹
            progress = None
            if parent_widget is not None:
                progress = QtWidgets.QProgressDialog(u"正在拷贝贴图...", u"中止", 0, len(copy_jobs), parent_widget)
                progress.setWindowModality(QtCore.Qt.WindowModal)
                progress.setValue(0)
                progress.show()

            canceled = False
            for index, (src_file, dst_file) in enumerate(copy_jobs, 1):
                dest_dir = os.path.dirname(dst_file)
                if not os.path.isdir(dest_dir):
                    os.makedirs(dest_dir)
                if need_copy(src_file, dst_file):
                    shutil.copy2(src_file, dst_file)
                    copied += 1

                if progress is not None:
                    progress.setValue(index)
                    QtCore.QCoreApplication.processEvents()
                    if progress.wasCanceled():
                        canceled = True
                        break

            if progress is not None:
                progress.deleteLater()

            if canceled:
                return u"拷贝被中止，贴图路径未替换，请重新检查后再修复"

        # 全部拷完后再统一替换路径。原属性值是具体文件名（UDIM 的某一块、序列的某一帧）时
        # 保持这种写法，Maya 会按 uvTilingMode / useFrameExtension 自己解析；原来就是
        # 占位符写法的则保留占位符
        def replace_paths():
            for info in outside + relative:
                dest_dir = info['dest_dir']
                raw_name = os.path.basename(info['raw_path'].replace('\\', '/'))
                suffix = info.get('suffix', '')
                copied_raw_name = add_suffix(raw_name, suffix) if suffix else raw_name
                if TOKEN_PATTERN.search(raw_name) or not os.path.isfile(dest_dir + '/' + copied_raw_name):
                    raw_name = os.path.basename(info['pattern'])
                if suffix:
                    raw_name = add_suffix(raw_name, suffix)
                new_path = dest_dir + '/' + raw_name
                set_texture_path(info['node_attr'], new_path)
                logger.warning(u"AUTO FIX: {0}: {1} -> {2}".format(info['node_attr'], info['raw_path'], new_path))

        utils.executeInMainThreadWithResult(replace_paths)

        logger.info(u"共 {0} 个文件，实际拷贝 {1} 个，其余已存在且未变化。".format(len(copy_jobs), copied))
        if missing:
            logger.warning(u"另有 {0} 个贴图文件不存在，无法自动修复，请手动处理。".format(len(missing)))

    except Exception:
        return traceback.format_exc()
