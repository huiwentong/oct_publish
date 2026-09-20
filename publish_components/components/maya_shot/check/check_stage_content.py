# -*- coding: utf-8 -*-
import importlib
import re
import traceback

import maya.cmds as cmds
import maya.utils as utils

from oct_maya.tools.lay.usd_lay_manager_new.core import get_existing_asb_proxy, is_old_asb_architecture
from publish_components.utils.maya_utils import asb_build


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    检查 ASB stage 的 usda 内容是否为 USD Lay Manager 填入的标准结构：
    stage 不能为空，顶层 prim 必须是 def Xform + 1 条 no_tex reference（置空资产允许无 reference），
    prim 名需以引用的资产名开头
    """
    # 工具只会在 root layer 写出三种顶层 prim:
    #   A 正常资产: def Xform + 1 条 reference(<资产名>.no_tex.usda)
    #   B 置空资产: 同 A, 再加 active=false
    #   C 置空占位: def Xform + active=false, 无 reference (架构转换时找不到资产)
    # prim 名为 资产名 + 可选纯数字后缀 (重名自动加)。
    # usda 文件丢失时工具会自动重建空 stage, 艺术家没重新填入就会发布出空文件, 这里一并拦住。
    #
    # mayaUsd.lib / pxr.Sdf 用 importlib 动态导入：组件顶层 import 会被提到 CLI 脚本最前面，
    # 那时 mayaUsdPlugin 还没加载，直接写 import 会失败。
    try:
        no_tex_suffix = '.no_tex.usda'

        def check_top_prim(sdf, root_layer, prim):
            """按 root layer 的 prim spec 校验一个顶层 prim，返回错误原因列表"""
            errs = []
            prim_name = prim.GetName()
            spec = root_layer.GetPrimAtPath(prim.GetPath())

            if spec is None:
                errs.append(u"root layer 里没有该 prim 的定义（来自其他层），不是工具填入的资产")
            elif spec.specifier != sdf.SpecifierDef or spec.typeName != 'Xform':
                errs.append(u"不是 def Xform（可能是直接 import 进 stage 的几何体），请删除后用工具重新填入")
            else:
                ref_items = list(spec.referenceList.GetAddedOrExplicitItems())
                if not ref_items:
                    # 形态 C: 只有置空占位允许没有 reference
                    if prim.IsActive():
                        errs.append(u"没有引用任何资产且未置空，请删除该空 prim 或重新填入资产")
                elif len(ref_items) > 1:
                    errs.append(u"有 {0} 条 reference，工具填入的资产只会有 1 条".format(len(ref_items)))
                else:
                    ref_name = ref_items[0].assetPath.replace('\\', '/').rsplit('/', 1)[-1]
                    if not ref_name.endswith(no_tex_suffix):
                        errs.append(u"引用的不是 no_tex 文件: {0}，请用工具重新填入".format(ref_name))
                    else:
                        # prim 名规则与 verify_component_name 一致: 资产名 + 可选纯数字后缀
                        asset_name = ref_name[:-len(no_tex_suffix)]
                        if not re.match(r'^{0}\d*$'.format(re.escape(asset_name)), prim_name):
                            errs.append(u"prim 名与引用的资产名 {0} 不匹配，应为资产名或资产名+数字".format(asset_name))

                if 'xformOp:transform' not in spec.attributes:
                    errs.append(u"缺少 xformOp:transform，不是工具填入的结构，请用工具重新填入")

            return errs

        def check():
            asb_build.init_usd()
            maya_usd_lib = importlib.import_module('mayaUsd.lib')
            sdf = importlib.import_module('pxr.Sdf')

            if is_old_asb_architecture():
                return u"当前 Stage 为旧架构，请先转换为新架构"

            proxy_shape = get_existing_asb_proxy()
            if not proxy_shape:
                # 镜头没有 asb
                return ""

            stage = maya_usd_lib.GetPrim(proxy_shape).GetStage()
            if not stage:
                return u"无法获取 {0} 的 stage".format(proxy_shape)

            root_layer = stage.GetRootLayer()
            if root_layer.anonymous:
                return u"ASB stage 的 root layer 为匿名层（usda 文件曾丢失），请重新打开文件后用工具重新填入资产"

            if root_layer.subLayerPaths:
                return u"ASB stage 带有 subLayers，是 Bk/An 的场景结构，不是 layout 填入的结构:\n{0}".format(
                    '\n'.join(root_layer.subLayerPaths))

            # 置空资产 active=false，GetChildren 会跳过，必须用 GetAllChildren
            top_prims = stage.GetPseudoRoot().GetAllChildren()
            if not top_prims:
                asb_grp = cmds.listRelatives(proxy_shape, parent=True, fullPath=True)[0]
                return (u"ASB stage 为空，没有填入任何资产: {0}\n"
                        u"如果镜头确实没有 asb 请删除 {1} 组，否则请用 USD Lay Manager 重新填入".format(
                            root_layer.identifier, asb_grp))

            errors = []
            for prim in top_prims:
                errs = check_top_prim(sdf, root_layer, prim)
                if errs:
                    errors.append(u"{0}:\n  {1}".format(prim.GetPath(), '\n  '.join(errs)))

            if errors:
                return u"ASB stage 内容检查未通过:\n{0}".format('\n'.join(errors))
            return ""

        result = utils.executeInMainThreadWithResult(check)
        if result:
            return result
    except:
        return traceback.format_exc()
