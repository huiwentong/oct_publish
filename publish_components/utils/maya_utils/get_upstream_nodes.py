# -*- coding: utf-8 -*-


def iter_upstream(node, l_nodes):
    import pymel.core as pm
    if not pm.objExists(node):
        return
    if pm.nodeType(node) == 'mesh':
        return
    for n_name in pm.hyperShade(listUpstreamNodes=node):
        if n_name not in l_nodes:
            l_nodes.append(n_name)
            iter_upstream(n_name, l_nodes)
    return


def get_nodes(node):
    l_nodes = []
    iter_upstream(node, l_nodes)
    return l_nodes
