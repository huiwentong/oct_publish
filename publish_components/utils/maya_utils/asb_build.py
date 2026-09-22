# -*- coding: utf-8 -*-
"""ASB scene inspection and component collection; call from Maya's main thread."""
import importlib
import ntpath
import os
import shutil

import maya.cmds as cmds


def init_usd() -> None:
    """Load USD and retain the separate Maya/USD save policy of the assembly tool."""
    if not cmds.pluginInfo('mayaUsdPlugin', query=True, loaded=True):
        cmds.loadPlugin('mayaUsdPlugin', quiet=True)
    cmds.optionVar(iv=('mayaUsd_SerializedUsdEditsLocation', 1))
    cmds.optionVar(iv=('mayaUsd_SerializedUsdEditsLocationPrompt', 0))


def usd_modules() -> tuple:
    """Resolve USD Python modules after the Maya plugin has loaded its search paths."""
    return tuple(importlib.import_module('pxr.' + name) for name in ('Gf', 'Sdf', 'Usd', 'UsdGeom'))


def scene_info(entity_name: str) -> tuple:
    """Return the asset root, legacy-layout flag and its proxy shapes."""
    init_usd()
    root = '|' + entity_name
    if not cmds.objExists(root) or cmds.nodeType(root) != 'transform':
        raise RuntimeError('找不到当前 ASB 资产根组: ' + root)
    children = cmds.listRelatives(root, children=True, fullPath=True) or []
    legacy = any(cmds.nodeType(node) != 'mayaUsdProxyShape' for node in children)
    proxies = cmds.listRelatives(root, allDescendents=True, fullPath=True,
                                 type='mayaUsdProxyShape') or []
    if not proxies:
        raise RuntimeError('ASB 根组下没有 mayaUsdProxyShape: ' + root)
    if not legacy and len(proxies) != 1:
        raise RuntimeError('新版 ASB 必须只有一个 Stage: ' + root)
    return root, legacy, proxies


def stage_for(proxy: str) -> object:
    """Get the live stage, including edits made in the current Maya session."""
    stage = importlib.import_module('mayaUsd.ufe').getStage(proxy)
    if stage is None:
        raise RuntimeError('无法读取 USD Stage: ' + proxy)
    return stage


def relative_usd_path(path: str, maya_file: str) -> str:
    """Validate the single-stage sidecar path without stripping absolute/traversal prefixes."""
    normalized = path.replace('\\', '/')
    if ntpath.isabs(normalized) or ntpath.splitdrive(normalized)[0]:
        raise RuntimeError('USD 必须使用相对路径: ' + path)
    while normalized.startswith('./'):
        normalized = normalized[2:]
    expected = expected_relative_usd_path(maya_file)
    if normalized.lower() != expected.lower():
        raise RuntimeError('USD 路径应为 {0}，当前为 {1}'.format(expected, path))
    return normalized


def expected_relative_usd_path(maya_file: str) -> str:
    """Return the required USD sidecar path for a Maya publish file."""
    basename = ntpath.splitext(ntpath.basename(maya_file))[0]
    return 'maya_usd/' + basename + '.usda'


def repair_proxy_paths(proxies: list, maya_file: str) -> tuple:
    """Copy a mismatched sidecar when needed and point proxies at the required relative path."""
    expected_relative = expected_relative_usd_path(maya_file)
    maya_directory = ntpath.dirname(ntpath.abspath(maya_file))
    expected_absolute = ntpath.normpath(
        ntpath.join(maya_directory, *expected_relative.split('/'))
    )
    repairs = []
    for proxy in proxies:
        current_path = cmds.getAttr(proxy + '.filePath') or ''
        try:
            relative_usd_path(current_path, maya_file)
            continue
        except RuntimeError:
            pass

        layer = stage_for(proxy).GetRootLayer()
        if layer.dirty:
            raise RuntimeError('请先保存 USD 修改后再修复路径: ' + proxy)

        normalized = current_path.replace('/', ntpath.sep)
        if ntpath.isabs(normalized) or ntpath.splitdrive(normalized)[0]:
            attribute_path = ntpath.normpath(normalized)
        else:
            attribute_path = ntpath.normpath(ntpath.join(maya_directory, normalized))
        candidates = [
            getattr(layer, 'realPath', ''),
            getattr(layer, 'identifier', ''),
            attribute_path,
        ]
        source_path = next((ntpath.normpath(path) for path in candidates
                            if path and not str(path).startswith('anon:')
                            and os.path.isfile(path)), '')

        if not os.path.isfile(expected_absolute):
            if not source_path:
                raise RuntimeError(
                    '找不到可用于修复的 USD 文件: {0} ({1})'.format(proxy, current_path)
                )
            os.makedirs(ntpath.dirname(expected_absolute), exist_ok=True)
            shutil.copy2(source_path, expected_absolute)

        cmds.setAttr(proxy + '.filePath', expected_relative, type='string')
        repairs.append((proxy, current_path, expected_relative))

    return repairs, proxy_paths(proxies, maya_file)


def proxy_paths(proxies: list, maya_file: str) -> list:
    """Validate every proxy and return unique relative sidecar paths."""
    paths = []
    for proxy in proxies:
        path = relative_usd_path(cmds.getAttr(proxy + '.filePath') or '', maya_file)
        if path not in paths:
            paths.append(path)
    return paths


def collect_components(entity_name: str) -> dict:
    """Collect legacy multi-stage or single-stage assembly data in AsbStepUsd format."""
    root, legacy, proxies = scene_info(entity_name)
    Gf, Sdf, Usd, UsdGeom = usd_modules()
    components = {}
    for proxy in proxies:
        stage = stage_for(proxy)
        layer = stage.GetRootLayer()
        roots = stage.GetPseudoRoot().GetChildren()
        if not roots:
            raise RuntimeError('USD Stage 没有根 Prim: ' + proxy)
        legacy_reference = ''
        if legacy:
            if not layer.subLayerPaths:
                raise RuntimeError('旧版 Stage 缺少资产 subLayer: ' + proxy)
            legacy_reference = layer.ComputeAbsolutePath(layer.subLayerPaths[0])
        for prim in stage.Traverse():
            transform = {}
            usd_file = ''
            if legacy:
                if not prim.HasAttribute('usd_path'):
                    continue
                path = prim.GetAttribute('usd_path').Get()
                if prim == roots[0]:
                    usd_file = legacy_reference
                imported = prim.GetAttribute('import_xform').Get()
                for op in UsdGeom.Xformable(prim).GetOrderedXformOps():
                    if op.GetOpName() == 'xformOp:transform':
                        matrix = op.Get()
                        if matrix is not None and (imported is None or any(
                                abs(matrix[i][j] - imported[i][j]) > 1e-6
                                for i in range(4) for j in range(4))):
                            transform = {'xform': [matrix[i][j] for i in range(4) for j in range(4)]}
                        break
            else:
                if not Usd.ModelAPI(prim).GetKind():
                    continue
                path = '/' + entity_name + prim.GetPath().pathString
                spec = layer.GetPrimAtPath(prim.GetPath())
                if spec:
                    refs = (list(spec.referenceList.prependedItems)
                            or list(spec.referenceList.appendedItems))
                    if refs:
                        wrapper = Sdf.Layer.FindOrOpen(layer.ComputeAbsolutePath(refs[0].assetPath))
                        if not wrapper or not wrapper.subLayerPaths:
                            raise RuntimeError('无法解析子资产 no_tex USD: ' + path)
                        usd_file = wrapper.ComputeAbsolutePath(wrapper.subLayerPaths[0])
                    if 'xformOp:transform' in spec.attributes:
                        matrix = spec.attributes['xformOp:transform'].default
                        if matrix is not None and matrix != Gf.Matrix4d(1.0):
                            transform = {'xform': [matrix[i][j] for i in range(4) for j in range(4)]}
            if not path or not path.startswith('/' + entity_name + '/'):
                raise RuntimeError('Component 不属于当前资产: ' + str(path))
            visible = UsdGeom.Imageable(prim).GetVisibilityAttr().Get()
            # 深层 Prim 仅记录变换/隐藏覆盖。不能把字符串 invisible 当成“可见”。
            if len(path.strip('/').split('/')) > 2 and not transform and visible != 'invisible':
                continue
            if len(path.strip('/').split('/')) == 2 and not usd_file:
                raise RuntimeError('直接子资产缺少 USD 引用: ' + path)
            if path in components:
                raise RuntimeError('重复 Component 路径: ' + path)
            components[path] = dict(usd_path=path, usd_file=usd_file, transform=transform,
                                    visible=visible, component_name=path.strip('/').replace('/', '.'))
    if not components:
        raise RuntimeError('ASB 场景没有可发布的 Component')
    return components


def scene_texture_paths() -> list:
    """Read all scene file/aiImage texture patterns, preserving sequence and UDIM tokens."""
    paths = []
    for node in cmds.ls(type=['file', 'aiImage']) or []:
        if cmds.nodeType(node) == 'file':
            path = cmds.getAttr(node + '.computedFileTextureNamePattern')
        else:
            path = cmds.getAttr(node + '.filename')
        if path:
            if not ntpath.isabs(path):
                path = cmds.workspace(expandName=path)
            paths.append(path)
    return paths
