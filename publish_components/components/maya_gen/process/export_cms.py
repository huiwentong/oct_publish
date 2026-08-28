# -*- coding:utf-8 -*-

import traceback
import os

import maya.cmds as cmds
import maya.utils as utils
import maya.api.OpenMaya as om2
import json, shutil, os, sys


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
生成cms文件
    """
    try:
        def J_nodesInfo(filter=[]):
            # 用于存储最终查询得到的数据,每个节点为一个元素
            res = {}
            res['dgNodes'] = []
            res['dagNodes'] = []
            # 遍历所有节点,以节点全名为字段存储,方便后续比对文件
            dgIterator = om2.MItDependencyNodes(om2.MFn.kInvalid)
            mfnDagNode = om2.MFnDagNode()
            while (not dgIterator.isDone()):
                currentNodeInfo = {}
                mObject = dgIterator.thisNode()
                # 区分dg,dag分开保存
                if mObject.hasFn(107):
                    # 设置dag
                    mfnDagNode.setObject(mObject)
                    # 获取信息
                    if not mfnDagNode.isIntermediateObject:
                        currentNodeInfo['name'] = mfnDagNode.name()
                        currentNodeInfo['fullName'] = mfnDagNode.fullPathName()
                        currentNodeInfo['type'] = mObject.apiTypeStr[1].lower() + mObject.apiTypeStr[2:]
                        currentNodeInfo['child'] = []
                        if mfnDagNode.childCount() > 0:
                            for chIndex in range(0, mfnDagNode.childCount()):
                                chNodeTemp = om2.MFnDagNode(mfnDagNode.child(chIndex))
                                if not chNodeTemp.isIntermediateObject:
                                    currentNodeInfo['child'].append(chNodeTemp.name())
                        currentNodeInfo['parent'] = []
                        if mfnDagNode.parentCount() > 0:
                            for paIndex in range(0, mfnDagNode.parentCount()):
                                currentNodeInfo['parent'].append(
                                    om2.MFnDagNode(mfnDagNode.parent(paIndex)).fullPathName())
                        # 模型节点保存点线面信息
                        if currentNodeInfo['type'] == 'mesh':
                            mfnMesh = om2.MFnMesh(mObject)
                            currentNodeInfo['meshInfo'] = {}
                            currentNodeInfo['meshInfo']['numVertices'] = str(mfnMesh.numVertices)
                            currentNodeInfo['meshInfo']['numEdges'] = str(mfnMesh.numEdges)
                            currentNodeInfo['meshInfo']['numPolygons'] = str(mfnMesh.numPolygons)
                            currentNodeInfo['meshInfo']['numUVs'] = str(mfnMesh.numUVs())

                            sgTemp = cmds.listConnections(currentNodeInfo['fullName'], type="shadingEngine")
                            if sgTemp != None:
                                # 过滤重复sg节点
                                shadingEngineNodes = list(set(sgTemp))
                                currentNodeInfo['shadingEngineNodes'] = shadingEngineNodes
                                currentNodeInfo['materialNodes'] = []
                                if len(shadingEngineNodes) > 0:
                                    for seItem in shadingEngineNodes:
                                        mat = cmds.listConnections(seItem + ".surfaceShader")
                                        if mat is not None:
                                            for matItem in mat:
                                                if matItem not in currentNodeInfo['materialNodes']:
                                                    currentNodeInfo['materialNodes'].append(matItem)

                        # 根据过滤器筛选需要的类型
                        if len(filter) < 1:
                            res['dagNodes'].append(currentNodeInfo)
                        else:
                            if currentNodeInfo['type'] in filter:
                                res['dagNodes'].append(currentNodeInfo)
                else:
                    # 设置dg
                    mfnDgNode = om2.MFnDependencyNode(mObject)
                    # 获取信息
                    currentNodeInfo['name'] = mfnDgNode.name()
                    # currentNodeInfo['fullName']=mfnDgNode.fullPathName()
                    currentNodeInfo['type'] = mObject.apiTypeStr[1].lower() + mObject.apiTypeStr[2:]
                    if len(filter) < 1:
                        res['dgNodes'].append(currentNodeInfo)
                    else:
                        if currentNodeInfo['type'] in filter:
                            res['dgNodes'].append(currentNodeInfo)

                # 下一个对象.
                dgIterator.next()
            return res

        def process():
            cms_file = 'material_slots.cms'
            version_dir = process_data.get('version_dir', '')
            full_cms_file = version_dir + '/' + cms_file

            cms = {}
            cms['meshs'] = []
            for mitem in J_nodesInfo(['mesh'])['dagNodes']:
                if mitem['fullName'].find('|high|') > 0:
                    cms['meshs'].append(mitem)

            with open(full_cms_file, 'w') as f:
                f.write(json.dumps(cms, sort_keys=True, indent=4, separators=(",", ":")))

        return utils.executeInMainThreadWithResult(process)
    except:
        return traceback.format_exc()
