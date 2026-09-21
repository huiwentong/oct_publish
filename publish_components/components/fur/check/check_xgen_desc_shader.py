# -*- coding: utf-8 -*-
import traceback
import maya.cmds as cmds
import maya.mel as mel

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """检查 XGen Description 连接的材质是否为 Arnold 材质。"""
    try:
        def get_arnold_node_types():
            try:
                node_types=mel.eval('pluginInfo -q -dependNode "mtoa";') or []
            except Exception:
                return set()
            if isinstance(node_types,str):
                node_types=[node_types]
            return set(node_types)

        def check_shader_type_is_arnold(description,arnold_node_types):
            shapes=cmds.listRelatives(description,shapes=True) or []
            if not shapes:
                return True

            sg_nodes=cmds.listConnections(shapes[0],type="shadingEngine") or []
            if not sg_nodes:
                return True

            sg=sg_nodes[0]
            shaders=cmds.listConnections(sg+".aiSurfaceShader",source=True,destination=False) or []
            if not shaders:
                shaders=cmds.listConnections(sg+".surfaceShader",source=True,destination=False) or []
            if not shaders:
                return True

            return cmds.nodeType(shaders[0]) in arnold_node_types

        palette=process_data.get("xgen_palette_name")
        descriptions=process_data.get("xgen_descriptions",[])

        if not palette:
            raise RuntimeError(u"没有获取到 XGen Palette 信息")
        if not descriptions:
            raise RuntimeError(u"没有获取到 XGen Description 信息")

        arnold_node_types=get_arnold_node_types()
        if not arnold_node_types:
            raise RuntimeError(u"无法获取 mtoa Arnold 节点类型，请检查 Arnold 插件是否加载")

        bad_descriptions=[]
        for description in descriptions:
            if not check_shader_type_is_arnold(description,arnold_node_types):
                bad_descriptions.append(description.split("|")[-1])

        if bad_descriptions:
            raise RuntimeError(u"连接了非 Arnold 材质：\n{}".format("\n".join(bad_descriptions)))

        if logger:
            logger.info(u"XGen Arnold 材质检查通过")
    except Exception:
        return traceback.format_exc()