# -*- coding: utf-8 -*-
import traceback
import xgenm as xg
import maya.cmds as cmds
import maya.utils as utils

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """检查 XGen Description 连接的材质是否为 Arnold 材质。"""
    try:
        def check_shader_type_is_arnold(desc):
            shp = cmds.listRelatives(desc, shapes=1)[0]
            sg = cmds.listConnections(shp, source=1, destination=1, connections=0, plugs=0, type='shadingEngine')
            if sg:
                sg = sg[0]
                shader = cmds.listConnections(sg + '.aiSurfaceShader', source=1, destination=0, connections=0, plugs=0)
                if not shader:
                    shader = cmds.listConnections(sg + '.surfaceShader', source=1, destination=0, connections=0, plugs=0)

                if shader:
                    # 列出所有arnold节点
                    arnold_node_types = cmds.pluginInfo('mtoa', q=True, dependNode=True)
                    shader_type = cmds.nodeType(shader[0])
                    if shader_type not in arnold_node_types:
                        return False
            return True

        def check():
            bad_desc = []
            palettes = xg.palettes()
            palette_num = len(palettes)
            if palette_num != 1:
                return u"xgen palette数量不是一个， 请检查"
            palette = palettes[0]
            for desc in xg.descriptions(palette):
                if not check_shader_type_is_arnold(desc):
                    bad_desc.append(desc)

            if bad_desc:
                return u'连接了非Arnold材质：\n\t{}'.format(bad_desc)
            else:
                return None

        result = utils.executeInMainThreadWithResult(check)
        if result:
            return result

    except Exception:
        return traceback.format_exc()