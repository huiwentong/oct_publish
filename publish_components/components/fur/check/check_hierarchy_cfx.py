# -*- coding: utf-8 -*-
import traceback
import xgenm as xg
import pymel.core as pm
import maya.utils as utils
from publish_components.utils.maya_utils import dialogs

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """检查cfx资产层级"""
    try:
        CFX_FUR_TEMPLATE = \
            [
                {'PATH': '|Root_grp|Geo_grp',                                           'CAN NOT FIX': True},
                {'PATH': '|Root_grp|Hair_cfx',                                          'CONTAIN TYPES': ['xgmPalette']},
                {'PATH': '|Root_grp|Hair_cfx|Hair_curves'},
                {'PATH': '|Root_grp|Hair_cfx|Hair_curves|Hair_curves_base'},
                {'PATH': '|Root_grp|Hair_cfx|Hair_curves|Hair_curves_cfx'},
                {'PATH': '|Root_grp|Hair_cfx|Hair_xgenBaseGeo',                         'CONTAIN TYPES': ['xgmSubdPatch.geometry']},
                {'PATH': '|Root_grp|Hair_cfx|Hair_xgenBaseGeo_wrapNode'},
                {'PATH': '|Root_grp|Hair_cfx|Hair_dyn',                                 'CONTAIN TYPES': ['hairSystem', 'nucleus']},
                {'PATH': '|Root_grp|Hair_cfx|base',                                     'CONTAIN TYPES': ['wrap.basePoints']},
            ]

        def check():
            errorLst = []
            for _item in CFX_FUR_TEMPLATE:
                _path = _item.get('PATH')
                _contarinTypes = _item.get('CONTAIN TYPES', [])
                _name = _path.split('|')[-1]
                _parent = _path.rsplit('|', 1)[0]

                nodes = pm.ls(_name)
                if len(nodes) == 0:
                    errorLst.append(u'不存在 {} 节点'.format(_name))
                elif len(nodes) > 1:
                    errorLst.append(u'存在重名 {} 节点： '.format(_name) + ' '.join([str(n) for n in nodes]))
                else:
                    node = nodes[0]
                    if _parent not in node.fullPath():
                        errorLst.append(u'{} 节点不在 {} 组下'.format(_name, _parent))
                    for ct in _contarinTypes:
                        if '.' in ct:
                            _type, _attr = ct.split('.')
                            for _nodeOfTheType in pm.ls(type=_type):
                                for _connectedNode in pm.listConnections(_nodeOfTheType.attr(_attr)):
                                    if 'dagNode' not in pm.nodeType(_connectedNode, inherited=1):
                                        continue
                                    if _path not in _connectedNode.fullPath():
                                        errorLst.append(u'{} 节点不在 {} 组下'.format(_connectedNode, _path))
                        else:
                            _type = ct
                            for _nodeOfTheType in pm.ls(type=_type):
                                if _path not in _nodeOfTheType.fullPath():
                                    errorLst.append(u'{} 节点不在 {} 组下'.format(_nodeOfTheType, _path))
            return errorLst

        errors = utils.executeInMainThreadWithResult(check)
        if errors:
            return str(errors)

    except Exception:
        return traceback.format_exc()

def fix(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """创建缺失的 Fur 核心层级节点。"""
    try:
        CFX_FUR_TEMPLATE = \
            [
                {'PATH': '|Root_grp|Geo_grp',                                           'CAN NOT FIX': True},
                {'PATH': '|Root_grp|Hair_cfx',                                          'CONTAIN TYPES': ['xgmPalette']},
                {'PATH': '|Root_grp|Hair_cfx|Hair_curves'},
                {'PATH': '|Root_grp|Hair_cfx|Hair_curves|Hair_curves_base'},
                {'PATH': '|Root_grp|Hair_cfx|Hair_curves|Hair_curves_cfx'},
                {'PATH': '|Root_grp|Hair_cfx|Hair_xgenBaseGeo',                         'CONTAIN TYPES': ['xgmSubdPatch.geometry']},
                {'PATH': '|Root_grp|Hair_cfx|Hair_xgenBaseGeo_wrapNode'},
                {'PATH': '|Root_grp|Hair_cfx|Hair_dyn',                                 'CONTAIN TYPES': ['hairSystem', 'nucleus']},
                {'PATH': '|Root_grp|Hair_cfx|base',                                     'CONTAIN TYPES': ['wrap.basePoints']},
            ]

        def repair():
            for _item in CFX_FUR_TEMPLATE:
                _path = _item.get('PATH')
                _contarinTypes = _item.get('CONTAIN TYPES', [])
                _name = _path.split('|')[-1]
                _parent = _path.rsplit('|', 1)[0]

                nodes = pm.ls(_name)
                if len(nodes) == 0:
                    pm.createNode('transform', name=_name)
                elif len(nodes) > 1:
                    pm.select(nodes)
                    return u'请检查重名节点：' + ' '.join([str(n) for n in nodes])

                node = pm.PyNode(_name)
                if _parent not in node.fullPath():
                    pm.parent(_name, _parent)
                for ct in _contarinTypes:
                    if '.' in ct:
                        _type, _attr = ct.split('.')
                        for _nodeOfTheType in pm.ls(type=_type):
                            for _connectedNode in pm.listConnections(_nodeOfTheType.attr(_attr)):
                                if 'dagNode' not in pm.nodeType(_connectedNode, inherited=1):
                                    continue
                                if _path not in _connectedNode.fullPath():
                                    pm.parent(_connectedNode, _path)
                    else:
                        _type = ct
                        for _nodeOfTheType in pm.ls(type=_type):
                            if _path not in _nodeOfTheType.fullPath():
                                pm.parent(_nodeOfTheType, _path)
            return None

        errors = utils.executeInMainThreadWithResult(repair)
        if errors:
            return errors

        logger.info("AUTO FIX: 自动修复成功！请检查是否正确！！")

    except Exception:
        return traceback.format_exc()