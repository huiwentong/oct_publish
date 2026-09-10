# -*- coding:utf-8 -*-
import re
from collections import OrderedDict

import maya.cmds as cmds
import pymel.core as pm


def is_mesh_transform(node):
    """
    判断节点是否有shape节点，且shape节点是否为mesh类型
    Args:
        node: PyNode 对象
    """
    if node.getShape() and node.getShape().type() == 'mesh':
        return True
    return False


def is_group_contain_mesh(children):
    """
    判断列表中的节点是否包含mesh类型
    Args:
        children: list, 组内所有子节点
    """
    for child in children:
        if is_mesh_transform(child):
            return True
    return False


def get_gen_asset_data(assets_dict):
    """
    获取 gen_asset.json 格式的数据，使用 OrderedDict， 以prop优先，按照层级深度倒序排序。

    Args:
        assets_dict: dict, 资产字典，key为节点longName，value为类型（'PROP'或'ASB'）
    Returns:
        dict, 资产数据，格式为:
        {
            "asset_name": {
                "id": 资产id,
                "asset_name": 资产名,
                "asset_type": 资产类型 PROP | ASB,
                "longname": 资产longname,
                "sub_assets": [longname1, longname2, ...],
            }
            ...
        }
    """

    # 定义一个函数，计算层级深度
    def depth(k):
        # 以 '|' 拆分后统计非空段的数量；支持前导'|'
        return sum(1 for seg in k.split('|') if seg)

    # 使用OrderedDict存储数据，保持原始顺序
    gen_asset_data = OrderedDict()

    # 为每个子资产排序，prop优先，按照层级深度倒序排序，列表里仅存储longname
    sort_name_list = sorted(list(assets_dict.keys()),
                            key=lambda k: (assets_dict[k] != 'PROP', -depth(k), k))
    

    # 遍历排序后的列表，生成 gen_asset.json 格式的数据
    for name in sort_name_list:
        asset_name = name.split('|')[-1]
        gen_asset_data.setdefault(key=asset_name,
                                  default={
                                    'id': None,
                                    'asset_name': asset_name,
                                    'asset_type': assets_dict[name],
                                    'longname': name,
                                    'sub_assets': []
                                  })
        
        if assets_dict[name] == 'ASB':
            # 如果是ASb类型，获取所有子层级资产
            sub_assets = [i for i in assets_dict if i.startswith(name) and i != name]
            chird_group = cmds.listRelatives(name, children=True, fullPath=True)
            sub_assets = [i for i in sub_assets if i in chird_group]
            gen_asset_data[asset_name]['sub_assets'] = sub_assets
    
    return gen_asset_data


def get_all_asset_group(group_object, publish_only=True):
    """
    递归获取资产层级结构，将含有mesh的分组标记为'PROP'，其余分组标记为'ASB'

    优先读取 ASB场景拆分管理器 写在节点 notes 里的标记：人工指定为 Prop 的层级
    按 Prop 拆分，标记为不发布的层级不参与发布。没有装管理器时按层级结构判定。

    Args:
        group_object: PyNode 对象
        publish_only: 为 True 时剔除标记为不发布的层级；命名检查需要全量层级时传 False
    returns:
        dict, 资产字典，key为节点longName，value为类型（'PROP'或'ASB'）
        {
            "longname1": "PROP",
            "longname2": "ASB",
            "longname3": "PROP",
            ...
        }
    """
    try:
        from oct_maya.tools.mod.asb_split_tool import api
    except ImportError:
        api = None

    if api:
        return api.get_asset_group_dict(root_path=group_object.longName(),
                                        publish_only=publish_only)

    return get_asset_group_by_structure(group_object)


def get_env_placeholders(root_longname, project_name):
    """
    获取 ASB场景拆分管理器 写在场景里的 ENV 占位，按父层级归类。

    ENV 占位在场景里只是一个空组，不拆分发布，也不建资产，只在 ASB 组装 USD 时
    作为一个 component 引用进去。引用的是 ENV 资产目录下不带版本号的 asb usda，
    由资产自己每次发布时更新 —— 所以资产还没发布时先占位也没关系，文件不存在时
    USD 只告警不报错，等它发布完总 ASB 打开就有内容了。

    Args:
        root_longname: str, ASB 根层级的 longname
        project_name: str, 项目名

    Returns:
        dict, {父层级longname: [{'longname', 'asset_name', 'asset_id', 'usd_file'}, ...]}
        没有装拆分管理器或场景里没有占位时返回空字典
    """
    try:
        from oct_maya.tools.mod.asb_split_tool import api
    except ImportError:
        return {}

    placeholders = {}
    for longname, env in api.get_env_placeholders(root_path=root_longname).items():
        usd_file = api.env_asset_usda(project_name, env['asset_name'])
        if not usd_file:
            print(u'>>>> ENV占位 {0} 取不到usd路径，跳过'.format(longname))
            continue
        placeholders.setdefault(env['parent'], []).append({
            'longname': longname,
            'asset_name': env['asset_name'],
            'asset_id': env['asset_id'],
            'usd_file': usd_file,
        })

    return placeholders


def get_asset_group_by_structure(group_object):
    """
    只按层级结构递归判定资产类型，不读取拆分管理器的标记。

    Args:
        group_object: PyNode 对象
    returns:
        dict, 资产字典，key为节点longName，value为类型（'PROP'或'ASB'）
    """

    assets_dict = {group_object.longName(): 'ASB'}

    children = pm.listRelatives(group_object, children=True)
    if not children:
        return assets_dict

    if is_group_contain_mesh(children):
        assets_dict[group_object.longName()] = 'PROP'
        return assets_dict
    else:
        for child in children:
            assets_dict[child.longName()] = 'ASB'
            assets_dict.update(get_asset_group_by_structure(child))

    return assets_dict


def ends_with_digit(s):
    # 如果末尾是数字，返回 True；否则 False
    return bool(re.search(r'\d$', s))


def check_prefix_parts(prefix, asset_name):
    """
    按下划线逐段校验前缀是不是父级资产名的缩写。

    缩写要分段对位取：前缀第一段只能用父级第一段里出现过的字符，第二段只能用
    第二段的，不允许跨段取字符。比如父级 temp_a，tmp_a 合法（tmp 取自 temp、
    a 取自 a）；tmp_p 不合法（p 来自第一段 temp）；tma_a 也不合法（tma 里的 a
    来自第二段）。

    Args:
        prefix: str, 子层级名中属于前缀的部分
        asset_name: str, 父级资产名

    Returns:
        str, 不规范时返回说明文本，规范时返回空字符串
    """
    prefix_parts = [part for part in prefix.split('_') if part]
    asset_parts = [part for part in asset_name.split('_') if part]

    if len(prefix_parts) != len(asset_parts):
        return u'前缀 {0} 有 {1} 段，与父级资产名 {2} 的 {3} 段对不上'.format(
            prefix.strip('_'), len(prefix_parts), asset_name, len(asset_parts))

    for prefix_part, asset_part in zip(prefix_parts, asset_parts):
        invalid = [char for char in prefix_part if char not in asset_part]
        if invalid:
            return u'缩写 {0} 中的 {1} 不属于父级的 {2}，缩写要按下划线分段取'.format(
                prefix_part, ' '.join(invalid), asset_part)

    return ''


def check_group_name(longname):
    """
    传入参数longname, 比如 |city_all|ct_dimian|ct_dm_cube|ct_dm_cb_box
    判断该层级的命名是否符合规范。(规范: 子层的命名前缀，必须是父层级的名称简写，
    且缩写按下划线分段对位取，不能跨段取字符: temp_a -> tmp_a 合法,
    tmp_p、tma_a 都不合法)
    并且名字结尾不能含有数字。

    Args:
        longname: str, 节点longname
    
    Returns:
        bool, 符合规范返回True, 否则错误信息的字符串
        str, 错误信息
    """

    nodes = longname.strip('|').split('|')

    # 检查每个节点末尾是否是数字
    for node in nodes:
        if ends_with_digit(node):
            return u"节点 {0} 命名末尾不能是数字".format(node)

    top = nodes[0]
    asset_name = top[:-4] if top.endswith('_all') else top
    nodes[0] = asset_name
    underline_count = asset_name.count('_')
    latest_prefix = ''

    for _index, node in enumerate(nodes[1:]):
        underline_count += 1

        if underline_count != node.count('_'):
            return u"节点 {0} 命名中下划线数量不为 {1}，只允许比父级资产的下划线多一个".format(node, underline_count)

        prefix = '_'.join(node.split('_')[:underline_count])
        prefix = prefix.replace(latest_prefix, '', 1)
        latest_prefix += prefix
        name = node.replace(latest_prefix, '', 1)

        if name.count('_') > 1:
            return u"节点 {0} 命名中下划线数量不正确".format(node)

        prefix_error = check_prefix_parts(prefix, asset_name)
        if prefix_error:
            return u'节点 {0} 命名不规范：{1}'.format(node, prefix_error)

        asset_name = node.split('_')[-1]

    return True
