# -*- coding: utf-8 -*-
"""
贴图文件相关的通用工具：占位符路径展开、路径比较、文件名加后缀、文件哈希、文件头格式识别。

提交端的贴图检查和 Deadline 端的贴图拷贝共用，只依赖标准库（两个 Maya 相关函数在函数内
延迟导入 maya.cmds），可以在 mayapy 里安全导入。

Maya 自带的 fileTexturePathResolver.findAllFilesForPattern 每次都会把整个目录 listdir 一遍
再逐个 isfile，网络盘上贴图目录一大就非常慢。这里的 TextureFileResolver 对普通路径只做一次
isfile，带占位符的路径按目录缓存一次 scandir 结果，多个节点共用。

组件在 CLI 模式下会被 AST 平铺、丢掉模块级定义，所以贴图检查用到的常量和函数统一放在这里，
组件里只做 import。
"""
import hashlib
import os
import re

# Maya 贴图路径里的占位符 -> 匹配文件名用的正则。<u>/<U> 分别是 0 基和 1 基，大小写有区别；
# Arnold 的 aiImage 写的是小写 <udim>，和 <UDIM> 同义
TOKEN_REGEX = {
    '<f>': r'\d+',
    '<u>': r'[-+]?\d+',
    '<v>': r'[-+]?\d+',
    '<U>': r'[-+]?0*[1-9]+[0-9]*',
    '<V>': r'[-+]?0*[1-9]+[0-9]*',
    '<UDIM>': r'1(?:[0-9][0-9][1-9]|[1-9][1-9]0|0[1-9]0|[1-9]00)',
    '<udim>': r'1(?:[0-9][0-9][1-9]|[1-9][1-9]0|0[1-9]0|[1-9]00)',
}
TOKEN_PATTERN = re.compile('|'.join(re.escape(token) for token in TOKEN_REGEX))

# 贴图节点类型 -> 存路径的属性
TEXTURE_NODE_ATTRS = {'file': 'fileTextureName',
                      'aiImage': 'filename'}

# 发布允许的贴图扩展名，小写
ALLOWED_FORMATS = ('png', 'jpg', 'jpeg', 'tif', 'tiff', 'exr', 'tga', 'tx', 'hdr')

# 扩展名对应的实际文件格式。OpenImageIO 生成的 tx 通常使用 TIFF 容器。
EXPECTED_CONTENT_FORMATS = {
    'png': ('png',),
    'jpg': ('jpeg',),
    'jpeg': ('jpeg',),
    'tif': ('tiff',),
    'tiff': ('tiff',),
    'exr': ('exr',),
    'tga': ('tga',),
    'tx': ('tiff',),
    'hdr': ('hdr',),
}


def norm_path(path):
    """统一成正斜杠、去掉末尾斜杠的路径，方便比较和拼接。"""
    return os.path.normpath(path).replace('\\', '/').rstrip('/')


def is_under_dir(path, dir_path):
    """判断 path 是否在 dir_path 目录下（含子目录），Windows 路径不区分大小写。"""
    return (norm_path(path).lower() + '/').startswith(norm_path(dir_path).lower() + '/')


def add_suffix(name, suffix):
    """
    在文件名第一个 '.' 之前插入后缀，UDIM、序列帧的编号和占位符都保持在后面不动。

    a.jpg -> a_x.jpg
    tex.1001.png -> tex_x.1001.png
    tex.<UDIM>.png -> tex_x.<UDIM>.png

    Args:
        name: str, 文件名（不含目录）
        suffix: str, 要插入的后缀，不含下划线

    Returns:
        str, 加了后缀的文件名
    """
    stem, dot, rest = name.partition('.')
    return stem + '_' + suffix + dot + rest


def file_md5(file_path, block_size=1024 * 1024):
    """分块计算文件的 md5，避免大贴图一次读进内存。"""
    digest = hashlib.md5()
    with open(file_path, 'rb') as f:
        while True:
            block = f.read(block_size)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def files_md5(file_list):
    """
    计算一组文件（一套 UDIM 或序列帧）的整体 md5：按文件名排序后把各文件的 md5 串起来再算一次。
    """
    digest = hashlib.md5()
    for file_path in sorted(file_list, key=lambda p: os.path.basename(p).lower()):
        digest.update(file_md5(file_path).encode('ascii'))
    return digest.hexdigest()


def assign_collision_suffixes(groups, reserved_groups=None, hash_length=8):
    """
    按最终拷贝目标检测贴图冲突，并给需要改名的贴图组写入 ``suffix``。

    ``groups`` 中每项必须包含 ``files`` 和 ``dest_dir``。检测使用每个实际文件的
    目标路径，而不是贴图 pattern 的名字，因此能识别 UDIM / 序列与普通文件之间
    的冲突。``reserved_groups`` 只参与冲突检测，不会被改名，可用于保护工作目录里
    已经存在并被场景引用的贴图。

    Returns:
        int, 被分配后缀的贴图组数量
    """
    groups = list(groups)
    reserved_groups = list(reserved_groups or [])
    for info in groups:
        info['suffix'] = ''

    # {最终目标路径: [(贴图组, 源文件, 是否允许改名), ...]}
    by_destination = {}
    for info, mutable in [(item, True) for item in groups] + [
            (item, False) for item in reserved_groups]:
        dest_dir = norm_path(info['dest_dir'])
        for src_file in info['files']:
            dst_file = dest_dir + '/' + os.path.basename(src_file)
            key = os.path.normcase(os.path.normpath(dst_file))
            by_destination.setdefault(key, []).append((info, src_file, mutable))

    file_hash_cache = {}

    def content_hash(file_path):
        key = os.path.normcase(os.path.normpath(file_path))
        if key not in file_hash_cache:
            file_hash_cache[key] = file_md5(file_path)
        return file_hash_cache[key]

    conflict_ids = set()
    for dst_file, entries in by_destination.items():
        # 保护目标目录中已经存在的不同内容。源文件本身就是目标文件时不重复比较。
        source_keys = {os.path.normcase(os.path.normpath(src_file))
                       for _, src_file, _ in entries}
        has_external_destination = os.path.isfile(dst_file) and dst_file not in source_keys

        # 没有重名、目标也不存在时完全不读文件内容，避免给正常的大贴图发布增加开销。
        if len(entries) < 2 and not has_external_destination:
            continue

        hashes = {content_hash(src_file) for _, src_file, _ in entries}
        if has_external_destination:
            hashes.add(content_hash(dst_file))

        if len(hashes) > 1:
            conflict_ids.update(id(info) for info, _, mutable in entries if mutable)

    for info in groups:
        if id(info) in conflict_ids:
            info['suffix'] = files_md5(info['files'])[:hash_length]

    return len(conflict_ids)


def need_copy(src_file, dst_file):
    """目标不存在，或者大小、修改时间和源文件不一致时才需要拷贝。"""
    try:
        dst_stat = os.stat(dst_file)
    except OSError:
        return True
    src_stat = os.stat(src_file)
    return (src_stat.st_size != dst_stat.st_size
            or abs(src_stat.st_mtime - dst_stat.st_mtime) > 1)


def detect_texture_format(file_path):
    """
    根据文件头识别贴图的实际格式。

    Args:
        file_path: str, 贴图文件路径

    Returns:
        str, 识别出的格式；无法可靠识别时返回空字符串
    """
    try:
        with open(file_path, 'rb') as stream:
            header = stream.read(16)

            if header.startswith(b'DDS '):
                return 'dds'
            # JFIF 和 Exif 都是常见 JPEG 文件结构，不能把 JFIF 标记当成独立的非法格式。
            if header.startswith(b'\xff\xd8\xff'):
                return 'jpeg'
            if header.startswith(b'\x89PNG\r\n\x1a\n'):
                return 'png'
            if header.startswith((b'II*\x00', b'MM\x00*')):
                return 'tiff'
            if header.startswith(b'\x76\x2f\x31\x01'):
                return 'exr'
            if header.startswith((b'#?RADIANCE', b'#?RGBE')):
                return 'hdr'
            if header.startswith(b'8BPS'):
                return 'psd'
            if header.startswith((b'GIF87a', b'GIF89a')):
                return 'gif'
            if header.startswith(b'BM'):
                return 'bmp'
            if header.startswith(b'RIFF') and header[8:12] == b'WEBP':
                return 'webp'

            # TGA 2.0 的签名位于文件末尾；旧版 TGA 没有稳定签名，不做误判。
            stream.seek(0, os.SEEK_END)
            if stream.tell() >= 18:
                stream.seek(-18, os.SEEK_END)
                if stream.read(18).startswith(b'TRUEVISION-XFILE.'):
                    return 'tga'
    except (IOError, OSError):
        return ''

    return ''


class TextureFileResolver(object):
    """
    把贴图路径（可能带 <UDIM>、<f> 等占位符）展开成实际存在的文件列表。

    目录列表按目录缓存，同一个目录下不管有多少个贴图节点都只列一次。
    """

    def __init__(self):
        self._dir_cache = {}

    def list_dir(self, dir_name):
        """
        列出目录下的文件名，结果缓存。

        Returns:
            list, 文件名列表；目录不存在时为空列表
        """
        key = norm_path(dir_name).lower()
        if key in self._dir_cache:
            return self._dir_cache[key]

        names = []
        try:
            # scandir 的 is_file 直接用目录项自带的属性，不会对每个文件再 stat 一次
            with os.scandir(dir_name) as entries:
                names = [entry.name for entry in entries if entry.is_file()]
        except OSError:
            pass

        self._dir_cache[key] = names
        return names

    def find_files(self, pattern):
        """
        找出 pattern 对应的所有文件。

        Args:
            pattern: str, 绝对路径，文件名里可以带占位符

        Returns:
            list, 实际存在的文件绝对路径列表，找不到时为空列表
        """
        pattern = norm_path(pattern)
        dir_name, base_name = os.path.split(pattern)
        if not dir_name or not base_name:
            return []

        # 普通路径只做一次 isfile，不列目录
        if not TOKEN_PATTERN.search(base_name):
            return [pattern] if os.path.isfile(pattern) else []

        # 把占位符替换成正则，其余部分转义
        regex = ''
        cursor = 0
        for match in TOKEN_PATTERN.finditer(base_name):
            regex += re.escape(base_name[cursor:match.start()])
            regex += TOKEN_REGEX[match.group()]
            cursor = match.end()
        regex += re.escape(base_name[cursor:]) + '$'
        regex = re.compile(regex, re.IGNORECASE)

        return [dir_name + '/' + name for name in self.list_dir(dir_name) if regex.match(name)]


def resolve_texture_pattern(node, attr_name):
    """
    取得贴图节点的原始属性值和解析后的绝对路径模式。

    file 节点用 computedFileTextureNamePattern，Maya 会把 UDIM、序列帧解析成带占位符的
    绝对路径；aiImage 的 filename 本身就支持 <udim>，相对路径按当前工程展开。

    Args:
        node: str, 节点名
        attr_name: str, 存路径的属性名

    Returns:
        (str 原始属性值, str 绝对路径模式)，原始值为空时模式也为空
    """
    import maya.cmds as cmds

    raw_path = cmds.getAttr(node + '.' + attr_name) or ''
    if not raw_path.strip():
        return raw_path, ''

    if attr_name == 'fileTextureName':
        pattern = cmds.getAttr(node + '.computedFileTextureNamePattern') or raw_path
    else:
        pattern = raw_path

    pattern = pattern.replace('\\', '/')
    if not os.path.isabs(pattern):
        pattern = cmds.workspace(expandName=pattern)

    return raw_path, norm_path(pattern)


def set_texture_path(node_attr, new_path):
    """
    替换节点的贴图路径，并保持原来的色彩空间。

    改 fileTextureName 会触发 Maya 按文件名规则重新推断 colorSpace，所以先记下来再设回去。
    """
    import maya.cmds as cmds

    node = node_attr.split('.')[0]
    color_space = None
    if cmds.attributeQuery('colorSpace', node=node, exists=True):
        color_space = cmds.getAttr(node + '.colorSpace')

    cmds.setAttr(node_attr, lock=False)
    cmds.setAttr(node_attr, new_path, type='string')

    if color_space:
        cmds.setAttr(node + '.colorSpace', color_space, type='string')


# 文件名后缀取 md5 的前几位，足够区分又不会让文件名太长
HASH_LENGTH = 8


def get_asset_texture_nodes(n_root):
    """
    找出资产层级下用到的贴图节点，按 shadingEngine 的上游节点判断，与 maya_gen/copy_asset_images 一致。

    Args:
        n_root: PyNode, 资产根层级

    Returns:
        list, [(节点名, 属性名), ...]，去重
    """
    import pymel.core as pm

    from publish_components.utils.maya_utils import get_upstream_nodes

    root_path = n_root.fullPath() + '|'
    texture_nodes = []
    seen = set()
    for se in pm.ls(type='shadingEngine'):
        upstream = get_upstream_nodes.get_nodes(se)
        if not any(node_path.startswith(root_path) for node_path in upstream):
            continue
        for node_path in upstream:
            node = pm.PyNode(node_path)
            attr_name = TEXTURE_NODE_ATTRS.get(node.nodeType())
            if attr_name and node.name() not in seen:
                seen.add(node.name())
                texture_nodes.append((node.name(), attr_name))

    return texture_nodes


def group_textures(texture_nodes, resolver, logger):
    """
    按解析后的路径模式归并贴图节点，同一套贴图被多个节点引用时只处理一次。

    Returns:
        dict, {pattern小写: {'pattern', 'files', 'nodes': [(node_attr, raw_path), ...]}}
    """
    groups = {}
    for node, attr_name in texture_nodes:
        raw_path, pattern = resolve_texture_pattern(node, attr_name)
        if not pattern:
            continue

        key = pattern.lower()
        if key not in groups:
            files = resolver.find_files(pattern)
            if not files:
                logger.warning(u'贴图不存在，跳过: {0}.{1} = {2}'.format(node, attr_name, raw_path))
                groups[key] = None
            else:
                groups[key] = {'pattern': pattern, 'files': files, 'nodes': []}

        if groups[key]:
            groups[key]['nodes'].append((node + '.' + attr_name, raw_path))

    return {key: info for key, info in groups.items() if info}


def assign_suffixes(groups, logger):
    """
    找出文件名相同的贴图组，同名同内容的合并，同名不同内容的给每组分配哈希后缀。

    Args:
        groups: dict, group_textures 的结果，会就地给每组加上 'suffix' 键（没冲突为空字符串）
    """
    conflict_count = assign_collision_suffixes(groups.values(), hash_length=HASH_LENGTH)
    if not conflict_count:
        return

    logger.info(u'检测到实际输出文件名冲突，{0} 组贴图按哈希改名:'.format(conflict_count))
    for info in groups.values():
        if info['suffix']:
            logger.info(u'   {0} -> {1}'.format(
                info['pattern'], add_suffix(os.path.basename(info['pattern']), info['suffix'])))
