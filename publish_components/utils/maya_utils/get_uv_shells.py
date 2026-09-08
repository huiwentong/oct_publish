# -*- coding: utf-8 -*-

import pymel.core as pm
import maya.OpenMaya as om

def get_shells(n):
    n_name = n.name()
    selList = om.MSelectionList()
    selList.add(n_name)
    selListIter = om.MItSelectionList(selList, om.MFn.kMesh)
    pathToShape = om.MDagPath()
    selListIter.getDagPath(pathToShape)

    uvset = pm.polyUVSet(n_name, q=True, currentUVSet=True)[0]

    shapeFn = om.MFnMesh(pathToShape)
    shells = om.MScriptUtil()
    shells.createFromInt(0)
    # shellsPtr = shells.asUintPtr()
    nbUvShells = shells.asUintPtr()

    uvShellIds = om.MIntArray()  # The container for the uv shell Ids
    uArray = om.MFloatArray()  # array for U coords
    vArray = om.MFloatArray()  # array for V coords

    shapeFn.getUVs(uArray, vArray)
    shapeFn.getUvShellsIds(uvShellIds, nbUvShells, uvset)

    # shellCount = shells.getUint(shellsPtr)
    shells = {}
    for i, n in enumerate(uvShellIds):
        if not n in shells:
            # shells[n].append([uArray[i],vArray[i]])
            shells[n] = {'u': [], 'v': []}

        shells[n]['u'].append(uArray[i])
        shells[n]['v'].append(vArray[i])

    d_uv_shells = {}
    for i in shells.keys():
        d_uv_shells[i] = ((min(shells[i]['u']), max(shells[i]['u'])), (min(shells[i]['v']), max(shells[i]['v'])))

    return d_uv_shells


def cross_udim(bbox):
    for i in [0, 1]:
        v1, v2 = bbox[i]
        sum = int(v1 + v2)
        if sum == sum/2 * 2:
            sum += 1
        axis = float(sum) / 2.0
        if abs(v1 - axis) > 0.501:
            return True
        if abs(v2 - axis) > 0.501:
            return True
    return False


def get_udim_center(bbox):
    u_min, u_max = bbox[0]
    v_min, v_max = bbox[1]
    x = int((u_min + u_max) / 2)
    y = int((v_min + v_max) / 2)
    udim = 1000 + y * 10 + x + 1
    return udim

def get_udim_range(bbox):
    l_udims = []
    u_min, u_max = bbox[0]
    v_min, v_max = bbox[1]

    for x in range(int(u_min), int(u_max) + 1):
        for y in range(int(v_min), int(v_max) + 1):
            l_udims.append(1000 + y * 10 + x + 1)

    return l_udims