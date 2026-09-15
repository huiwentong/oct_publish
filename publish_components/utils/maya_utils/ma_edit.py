# -*- coding: utf-8 -*-
"""直接改写 .ma 文本的工具，发布镜头 / 资产时用来清理 mayaUsd 属性、改写 usda 引用路径。

迁移自老 publish_process/lay/edit_ma_file.py 的模块级函数。
"""
import re
from pathlib import Path

import maya.cmds as cmds


def get_mayausd_version():
    """返回 mayaUsdPlugin 的版本字符串，没加载会先加载。需在 Maya 主线程调用。"""
    plugin_name = 'mayaUsdPlugin'
    if not cmds.pluginInfo(plugin_name, q=True, loaded=True):
        cmds.loadPlugin(plugin_name)
    return cmds.pluginInfo(plugin_name, q=True, version=True) or '0.0.0'


def _version_tuple(version):
    """'0.25.0' -> (0, 25, 0)，非数字段按 0 处理"""
    parts = []
    for token in str(version).split('.'):
        digits = re.match(r'\d+', token)
        parts.append(int(digits.group()) if digits else 0)
    return tuple(parts)


def clean_mayausd_attrs_from_ma(ma_path, mayausd_version):
    """删除 .ma 里 mayaUsd 0.25 之后新增的 setAttr ".lymgr" / ".rcpl" 行，老版本插件打开会报错。

    Args:
        ma_path: .ma 文件路径
        mayausd_version: 当前 mayaUsdPlugin 版本，<= 0.25.0 时跳过

    Returns:
        (是否有改动, 说明文本)
    """
    if _version_tuple(mayausd_version) <= _version_tuple('0.25.0'):
        return False, u'MayaUSD 版本 {0} <= 0.25.0，跳过清理'.format(mayausd_version)

    with open(ma_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # 删除 setAttr ".lymgr" ...; 或 setAttr ".rcpl" ...; 不要求它们必须独占一行
    pattern = re.compile(
        r'^[ \t]*setAttr[ \t]+"(?:\.lymgr|\.rcpl)"[^\r\n;]*;[ \t]*\r?\n?',
        re.MULTILINE
    )
    new_content, count = pattern.subn('', content)
    if count == 0:
        return False, u'没有需要清理的 mayaUsd 属性'

    with open(ma_path, 'w', encoding='utf-8', newline='') as f:
        f.write(new_content)
    return True, u'清理了 {0} 行 mayaUsd 属性 (MayaUSD {1})'.format(count, mayausd_version)


def fix_maya_usd_path_drive(ma_path):
    """把 .ma 里 mayaUsdProxyShape 引用的 usda 路径改写成 <ma 所在目录>/maya_usd/<ma stem>.usda。

    发布目录里的 ma 引用的应该是同目录 maya_usd 下的 usda（I 盘），
    而不是工作目录（W 盘）里的那份。

    Returns:
        (是否有改动, 说明文本)
    """
    ma = Path(ma_path)
    new_usd_path = (ma.parent / 'maya_usd' / '{0}.usda'.format(ma.stem)).as_posix()

    with open(ma_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # 匹配包含 maya_usd 的行中、双引号包裹的 usda 路径，整体替换为指定路径
    usda_path_pattern = re.compile(r'"[^"\r\n]*maya_usd[^"\r\n]*\.usda"')

    lines = content.splitlines(keepends=True)
    count = 0
    for i, line in enumerate(lines):
        if 'maya_usd' not in line:
            continue
        new_line, n = usda_path_pattern.subn(lambda _: '"{0}"'.format(new_usd_path), line)
        if n:
            lines[i] = new_line
            count += n

    if count == 0:
        return False, u'没有找到 maya_usd 的 usda 路径'

    with open(ma_path, 'w', encoding='utf-8', newline='') as f:
        f.write(''.join(lines))
    return True, u'usda 路径改写为 {0}（{1} 处）'.format(new_usd_path, count)
