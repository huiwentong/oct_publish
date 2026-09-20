# -*- coding: utf-8 -*-
"""镜头文件里 mayaUsdProxyShape 引用路径的解析与校验，check_stage_file_path / copy_usd_file_to_v_dir 共用。

镜头工作文件的 Stage 必须引用同目录 maya_usd 下、与 Maya 文件同名的 usda：
    W:/.../lay/maya/s590005.lay.rough_layout.v003.ma
    W:/.../lay/maya/maya_usd/s590005.lay.rough_layout.v003.usda
filePath 可能是相对路径（./maya_usd/xxx.usda）也可能是绝对路径（新版 mayaUsd 插件默认行为）。
"""
import os

import maya.cmds as cmds

USD_RELATIVE_DIR = 'maya_usd'


def list_proxy_usd_paths():
    """返回场景中所有 [(proxy_shape 长名, filePath 属性值)]，没有 filePath 属性的跳过。需在 Maya 主线程调用。"""
    result = []
    for proxy_shape in cmds.ls(type='mayaUsdProxyShape', long=True) or []:
        if not cmds.attributeQuery('filePath', node=proxy_shape, exists=True):
            continue
        result.append((proxy_shape, cmds.getAttr(proxy_shape + '.filePath') or ''))
    return result


def normalize_usd_path(usd_path):
    """统一斜杠并去掉开头的 ./"""
    norm = usd_path.replace('\\', '/')
    while norm.startswith('./'):
        norm = norm[2:]
    return norm


def resolve_usd_abs_path(usd_path, work_dir):
    """把 filePath 解析成绝对路径：绝对路径原样返回，相对路径按工作文件目录拼接。"""
    norm = normalize_usd_path(usd_path)
    if os.path.isabs(norm) or os.path.splitdrive(norm)[0]:
        return norm
    return os.path.join(work_dir, norm).replace('\\', '/')


def expected_usd_path(maya_file):
    """工作文件对应的规范 usda 绝对路径"""
    work_dir = os.path.dirname(maya_file.replace('\\', '/'))
    stem = os.path.splitext(os.path.basename(maya_file))[0]
    return '{0}/{1}/{2}.usda'.format(work_dir.rstrip('/'), USD_RELATIVE_DIR, stem)


def validate_usd_path(usd_path, maya_file):
    """校验一个 filePath 是否指向规范位置，返回错误文本，正确返回空字符串。"""
    maya_file = maya_file.replace('\\', '/')
    work_dir = os.path.dirname(maya_file)
    # 比较前消除重复分隔符及 . / ..，避免等价路径被字符串比较误判。
    expected = os.path.normpath(expected_usd_path(maya_file)).replace('\\', '/')
    abs_path = os.path.normpath(resolve_usd_abs_path(usd_path, work_dir)).replace('\\', '/')

    if os.path.dirname(abs_path).lower() != os.path.dirname(expected).lower():
        return u"USD 文件必须位于 {0} 目录下，当前为: {1}".format(os.path.dirname(expected), usd_path)
    if os.path.basename(abs_path).lower() != os.path.basename(expected).lower():
        return u"应为 {0}，当前为: {1}".format(expected, usd_path)
    return ""
