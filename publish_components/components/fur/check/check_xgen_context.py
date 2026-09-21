# -*- coding: utf-8 -*-
import traceback
import maya.cmds as cmds
import maya.mel as mel

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """初始化 Fur XGen 公共检查数据，供后续 Check 复用。"""
    try:
        def ls_type(node_type):
            nodes=mel.eval('ls -long -type "{}";'.format(node_type)) or []
            if isinstance(nodes,str):
                nodes=[nodes]
            return nodes

        def get_description_data(description_nodes):
            description_names=[]
            description_transforms=[]

            for node in description_nodes:
                parents=cmds.listRelatives(node,parent=True,fullPath=True) or []
                if parents:
                    transform=parents[0]
                    name=transform.split("|")[-1]
                else:
                    transform=node
                    name=node.split("|")[-1]
                    if name.endswith("Shape"):
                        name=name[:-5]

                if name not in description_names:
                    description_names.append(name)
                if transform not in description_transforms:
                    description_transforms.append(transform)

            return description_names,description_transforms

        def get_bound_geometry(patches):
            bound_geometry=[]
            bound_geometry_shapes={}

            for patch in patches:
                geometries=cmds.listConnections(patch+".geometry",source=True,destination=False) or []

                for geo in geometries:
                    if cmds.nodeType(geo)=="mesh":
                        shape=geo
                        parents=cmds.listRelatives(shape,parent=True,fullPath=True) or []
                        if not parents:
                            continue
                        transform=parents[0]
                    else:
                        transform=geo
                        shapes=cmds.listRelatives(transform,shapes=True,noIntermediate=True,fullPath=True,type="mesh") or []
                        if not shapes:
                            continue
                        shape=shapes[0]

                    if transform not in bound_geometry:
                        bound_geometry.append(transform)

                    bound_geometry_shapes[transform]=shape

            return bound_geometry,bound_geometry_shapes

        palettes=ls_type("xgmPalette")
        if not palettes:
            raise RuntimeError(u"没有找到 XGen Palette")
        if len(palettes)!=1:
            raise RuntimeError(u"XGen Palette 数量不是一个，请检查：\n{}".format("\n".join(palettes)))

        description_nodes=ls_type("xgmDescription")
        if not description_nodes:
            raise RuntimeError(u"没有找到 XGen Description")

        descriptions,description_transforms=get_description_data(description_nodes)
        if not descriptions:
            raise RuntimeError(u"无法解析 XGen Description 名称")

        patches=ls_type("xgmSubdPatch")
        bound_geometry,bound_geometry_shapes=get_bound_geometry(patches)

        if not bound_geometry:
            raise RuntimeError(u"没有找到 XGen 绑定的生长面")

        palette_node=palettes[0]

        process_data["xgen_palette_node"]=palette_node
        process_data["xgen_palette_name"]=palette_node.split("|")[-1]
        process_data["xgen_descriptions"]=descriptions
        process_data["xgen_description_nodes"]=description_nodes
        process_data["xgen_description_transforms"]=description_transforms
        process_data["xgen_subd_patches"]=patches
        process_data["xgen_bound_geometry"]=bound_geometry
        process_data["xgen_bound_geometry_shapes"]=bound_geometry_shapes

        if logger:
            logger.info(u"XGen Context: palette={}, descriptions={}, patches={}, bound_geometry={}".format(
                process_data["xgen_palette_name"],
                len(descriptions),
                len(patches),
                len(bound_geometry)
            ))
    except Exception:
        return traceback.format_exc()