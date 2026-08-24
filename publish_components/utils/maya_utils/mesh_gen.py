import pymel.core as pm
import maya.utils as utils

CLEANUP_LAMINA_CHECK = (
    'polyCleanupArgList 4 '
    '{ "1","2","1","0","0","0","0","0","0",'
    '"1e-005","0","1e-005","0","1e-005","0","-1","1","0" };'
)

CLEANUP_LAMINA_DELETE = (
    'polyCleanupArgList 4 '
    '{ "1","1","0","0","0","0","0","0","0",'
    '"1e-005","0","1e-005","0","1e-005","0","-1","1","0" };'
)

CLEANUP_NON_MANIFOLD = (
    'polyCleanupArgList 4 '
    '{ "0","1","0","0","0","0","0","0","0",'
    '"1e-005","0","1e-005","0","1e-005","0","1","0","0" };'
)

CLEANUP_SHORT_EDGE = (
    'polyCleanupArgList 3 '
    '{ "0","1","1","0","0","0","0","0","0",'
    '"1e-005","1","1e-005","0","1e-005","0","1","0" };'
)

CLEANUP_HOLE_CHECK = (
    'polyCleanupArgList 4 '
    '{ "1","2","0","0","0","0","1","0","0",'
    '"1e-05","0","1e-05","0","1e-05","0","-2","0","0" };'
)

def mel_eval(command):
    return utils.executeInMainThreadWithResult(lambda: pm.mel.eval(command))

def clear_selection():
    utils.executeInMainThreadWithResult(lambda: pm.select(clear=True))

def select_nodes(ns):
    utils.executeInMainThreadWithResult(lambda: pm.select(ns, replace=True))

def disable_poly_select_constraint():
    utils.executeInMainThreadWithResult(lambda: pm.polySelectConstraint(disable=True))

def delete_empty_mesh(m):
    m_t = m.getParent()
    pm.delete(m)
    remaining_meshes = pm.listRelatives(m_t, children=True, type='mesh') or []
    if not remaining_meshes:
        pm.delete(m_t)

def normalize_mesh_name(m_n):
    if m_n.isIntermediateObject():
        return m_n
    n_t = m_n.getParent()
    ex_name = '{}Shape'.format(n_t.nodeName())
    if m_n.nodeName() != ex_name:
        m_n = pm.rename(m_n, ex_name)
    return m_n

def has_non_manifold(m):
    """
    检测 non-manifold vertex / edge。
    """
    return bool(pm.polyInfo(m, nonManifoldVertices=True, nonManifoldEdges=True))

def has_extremely_short_edge(m, limit=0.000010):
    """
    检测长度小于 limit 的边。
    """
    try:
        pm.select(m, replace=True)
        pm.polySelectConstraint(mode=3, type=0x8000, length=True, lengthbound=(0, limit))
        result = mel_eval('expandedSelection -depth 1 -expansionType "DG"')
        return bool(result)
    finally:
        disable_poly_select_constraint()
        clear_selection()

def find_lamina_faces():
    """
    检测重合面 / lamina face。
    """
    clear_selection()
    return mel_eval(CLEANUP_LAMINA_CHECK) or []

def delete_lamina_faces():
    """
    删除重合面。
    """
    mel_eval(CLEANUP_LAMINA_DELETE)

def delete_non_manifold(ms):
    """
    清理 non-manifold geometry。
    """
    if not ms:
        return

    select_nodes(ms)
    mel_eval(CLEANUP_NON_MANIFOLD)

def delete_short_edges(ms):
    """
    清理极短边。
    """
    if not ms:
        return

    try:
        select_nodes(ms)
        mel_eval(CLEANUP_SHORT_EDGE)
    finally:
        disable_poly_select_constraint()
        clear_selection()

def delete_history():
    """
    删除历史。
    """
    mel_eval('DeleteHistory;')

def find_hole_faces():
    """
    检测包含 hole 的 polygon face。
    """
    clear_selection()
    mel_eval(CLEANUP_HOLE_CHECK)
    return utils.executeInMainThreadWithResult(lambda: pm.ls(selection=True)) or []