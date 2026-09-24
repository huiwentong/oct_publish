# -*- coding: utf-8 -*-
import traceback
import xgenm as xg
import pymel.core as pm
import maya.utils as utils


def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """收集毛发的材质信息"""
    try:
        def get_material_map():
            palette = xg.palettes()[0]
            descriptions = xg.descriptions(str(palette))
            mat_map = {}
            for _des in descriptions:

                node = pm.PyNode(_des)
                dag_name = node.longName()

                if isinstance(node, pm.nt.Transform):
                    shapes = node.getShapes(noIntermediate=True)
                else:
                    shapes = [node]

                materials = set()
                for shape in shapes:
                    sg_nodes = shape.listConnections(type='shadingEngine')
                    for sg in sg_nodes:
                        mats = sg.surfaceShader.listConnections()
                        materials.update(mats)
                usd_des_path = dag_name.split('Hair_cfx|')[1].replace('|', '/')
                if not mat_map.get(list(materials)[0].name()):
                    mat_map[list(materials)[0].name()] = ['/hair_cfx/' + usd_des_path]
                else:
                    mat_map[list(materials)[0].name()].append('/hair_cfx/' + usd_des_path)

            process_data.update({"mat_map": mat_map})

        utils.executeInMainThreadWithResult(get_material_map)

    except Exception:
        return traceback.format_exc()
