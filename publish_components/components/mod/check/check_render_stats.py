# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查并设置mesh渲染属性"""
    try:
        CHECK_DICT = {
            'castsShadows': 1, 'receiveShadows': 1, 'holdOut': 0, 'motionBlur': 1, 'primaryVisibility': 1,
            'smoothShading': 1,
            'visibleInReflections': 1, 'visibleInRefractions': 1, 'doubleSided': 1, 'geometryAntialiasingOverride': 0,
            'shadingSamplesOverride': 0
        }
        n_root = process_data.get("root", "|Root_grp")
        for each_mesh in pm.listRelatives(n_root, ad=1, c=1, type='mesh', ni=True):
            for k, v in CHECK_DICT.items():
                if each_mesh.getAttr(k) != v:
                    logger.warning("AUTO FIX: 修复节点 '{}' 的 ‘{}’ 属性为 {}".format(str(each_mesh), k, str(v)))
                    each_mesh.setAttr(k, v)

    except Exception:
        return traceback.format_exc()
