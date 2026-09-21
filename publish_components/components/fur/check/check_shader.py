# -*- coding: utf-8 -*-
import traceback
import maya.mel as mel
import pymel.core as pm

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """检查 hairPhysicalShader 材质，并自动替换为 aiStandardHair。"""
    try:
        def get_hair_physical_shaders():
            nodes=mel.eval('ls -type "hairPhysicalShader";') or []
            if isinstance(nodes,str):
                nodes=[nodes]

            result=[]
            for node in nodes:
                try:
                    result.append(pm.PyNode(node))
                except Exception:
                    pass
            return result

        shader_nodes=get_hair_physical_shaders()
        if shader_nodes:
            if logger:
                logger.warning(u"存在 hairPhysicalShader 类型材质球：{}".format(
                    ", ".join(shader.name() for shader in shader_nodes)
                ))

            cant_fix=[]
            for shader in shader_nodes:
                old_name=shader.name()
                try:
                    color=shader.rootColorD.get()

                    shading_groups=[]
                    for node in shader.outputs():
                        if node.nodeType()=="shadingEngine" and node not in shading_groups:
                            shading_groups.append(node)

                    if not shading_groups:
                        cant_fix.append(old_name)
                        continue

                    if logger:
                        logger.warning(u"AUTO FIX: {} 替换为 aiStandardHair".format(old_name))

                    for sg in shading_groups:
                        try:
                            shader.outColor.disconnect(sg.surfaceShader)
                        except Exception:
                            pass

                    pm.delete(shader)

                    new_shader=pm.shadingNode("aiStandardHair",asShader=True,name=old_name)
                    new_shader.baseColor.set(color)

                    for sg in shading_groups:
                        new_shader.outColor.connect(sg.surfaceShader,force=True)

                except Exception:
                    cant_fix.append(old_name)

            if cant_fix:
                raise RuntimeError(u"以下 hairPhysicalShader 无法自动转换：{}".format(", ".join(cant_fix)))

        if logger:
            logger.info(u"hairPhysicalShader 检查完成")
    except Exception:
        return traceback.format_exc()