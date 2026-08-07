
from PySide2 import QtCore
import traceback
import os
from oct.utils.path import Path
from oct_hou import get_ass_file_path
import re
import hou
import oct_hou
import numpy as np


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
检查cfx绑定节点
    """
    try:
        def find_vellum_io(node: hou.SopNode):
            all_node = []
            for i in node.children():
                subnode: hou.SopNode = i
                if subnode.type().name() == 'vellumio::2.0':
                    all_node.append(subnode)

            return all_node

        def find_file_cache(node: hou.SopNode):
            all_node = []
            for i in node.children():
                subnode: hou.SopNode = i
                if subnode.type().name() in ['filecache::2.0', 'oct_filecache_2', 'labs_filecache::2.0']:
                    all_node.append(subnode)

            return all_node

        def check_cloth_sim(node: hou.SopNode):
            is_empty = True
            for _node in node.children():
                if not _node.name().startswith('Python'):
                    is_empty = False
                    break
            return is_empty

        def compare_nodes(in_node: hou.SopNode, out_node: hou.SopNode, hair=False):
            message = ''
            in_geo: hou.Geometry = in_node.geometry()
            out_geo: hou.Geometry = out_node.geometry()
            if not compare_geo(in_geo, out_geo, 'pointcount'):
                message += f'节点{in_node.name()}和节点{out_node.name()}点数不同！\n'
            if not compare_geo(in_geo, out_geo, 'primitivecount'):
                message += f'节点{in_node.name()}和节点{out_node.name()}面数不同！\n'
            if not compare_geo(in_geo, out_geo, 'vertexcount'):
                message += f'节点{in_node.name()}和节点{out_node.name()}顶点数不同！\n'
            if hair:
                if not compare_geo(in_geo, out_geo, 'path', False):
                    message += f'节点{in_node.name()}和节点{out_node.name()}path属性不同！\n'
                if not compare_geo(in_geo, out_geo, 'attachedXgenDesc', False):
                    message += f'节点{in_node.name()}和节点{out_node.name()}attachedXgenDesc不同！\n'
            return message

        def compare_geo(geo: hou.SopNode, geo2: hou.SopNode, attribname: str, intrinsic=True):
            if intrinsic:
                in_pc = geo.intrinsicValue(attribname)
                out_pc = geo2.intrinsicValue(attribname)
            else:
                in_pc = geo.findPrimAttrib(attribname).strings()
                out_pc = geo2.findPrimAttrib(attribname).strings()

            if in_pc != out_pc:
                return False
            else:
                return True

        def add_index_check(_node):
            high_sim: hou.SopNode = _node.node('extract_high')
            wrap_ok: hou.SopNode = _node.node('WRAP_OK')
            hair_in: hou.SopNode = _node.node('transform2')
            hair_out: hou.SopNode = _node.node('hair_curve_out')
            mesh_in: hou.SopNode = _node.node('oct_drive_cfx_gen_mesh2')
            mesh_out: hou.SopNode = _node.node('hair_mesh_out')

            check_wrap: hou.SopNode = _node.node('check_wrap')
            check_wrap1: hou.SopNode = _node.node('check_wrap1')
            check_wrap2: hou.SopNode = _node.node('check_wrap2')
            check_wrap3: hou.SopNode = _node.node('check_wrap3')

            if not check_wrap:
                check_wrap: hou.SopNode = _node.createNode('attribwrangle', 'check_wrap')
                cmd = 'int ori_index = point(1,"index",@ptnum);if(i@index != ori_index){error("has wrong index attribute");}'
                check_wrap.parm('snippet').set(cmd)
                insert_node(check_wrap, wrap_ok, 0, high_sim, 1)
            if not check_wrap1:
                check_wrap1: hou.SopNode = _node.createNode('attribwrangle', 'check_wrap1')
                cmd = 'int ori_index = point(1,"index",@ptnum);if(i@index != ori_index){error("has wrong index attribute");}'
                check_wrap1.parm('snippet').set(cmd)
                insert_node(check_wrap1, mesh_out, 0, mesh_in, 1)
            if not check_wrap2:
                check_wrap2: hou.SopNode = _node.createNode('attribwrangle', 'check_wrap2')
                check_wrap2.parm('class').set(1)
                cmd = 'int ori_index = prim(1,"pindex",@primnum);if(i@pindex != ori_index){error("has wrong index attribute");}'
                check_wrap2.parm('snippet').set(cmd)
                insert_node(check_wrap2, check_wrap, 0, high_sim, 1)
            if not check_wrap3:
                check_wrap3: hou.SopNode = _node.createNode('attribwrangle', 'check_wrap3')
                check_wrap3.parm('class').set(1)
                cmd = 'int ori_index = prim(1,"pindex",@primnum);if(i@pindex != ori_index){error("has wrong index attribute");}'
                check_wrap3.parm('snippet').set(cmd)
                insert_node(check_wrap3, check_wrap1, 0, mesh_in, 1)

        def insert_node(ins_node, main_innode, main_index, sec_innode, sec_index):
            ins_node.setPosition([main_innode.position().x() + 1, main_innode.position().y() - 1])
            for connection in main_innode.outputConnections():
                outnode: hou.SopNode = connection.outputNode()
                outindex = connection.inputIndex()
                outnode.setInput(outindex, ins_node)
            ins_node.setInput(main_index, main_innode)
            ins_node.setInput(sec_index, sec_innode)

        def check_unknown_import(p_node: hou.SopNode):
            message = ''
            for node in p_node.allSubChildren():

                if node.type().name() == 'alembic':
                    r_parm = node.parm('fileName').getReferencedParm()
                    if r_parm.node().path() != p_node.path():
                        message += f'\n存在非法alembic节点: {node.path()}'
                if node.type().name() == 'file':
                    r_parm = node.parm('file').getReferencedParm()
                    if (not r_parm.node().isInsideLockedHDA() and
                            r_parm.node().path() != p_node.path() and
                            r_parm.node().type().name() != 'vellumio::2.0'
                    ):
                        print(r_parm)
                        message += f'\n存在非法的file节点: {node.path()}'

            return message


        _node:hou.SopNode = hou.node(submit_data['rig_path'])

        aname = _node.parm('asset_name').eval()
        if not aname:
            return '节点没有资产名，请联系TD处理'
        if aname != oct_hou.TC['task']['entity']['name']:
            return '节点资产名不合规，请联系TD处理'


        high_sim: hou.SopNode = _node.node('extract_high')
        wrap_ok: hou.SopNode = _node.node('WRAP_OK')
        hair_in: hou.SopNode = _node.node('transform2')
        hair_out: hou.SopNode = _node.node('hair_curve_out')
        mesh_in: hou.SopNode = _node.node('oct_drive_cfx_gen_mesh2')
        mesh_out: hou.SopNode = _node.node('hair_mesh_out')
        cloth_sim = _node.node('oct_build_cloth_sim')
        hair_sim = _node.node('oct_build_hair_sim2')



        if find_file_cache(cloth_sim) or find_file_cache(hair_sim) or find_file_cache(_node):
            return f"解算节点中不应该有filecache节点，请在发布前清理这些节点！:{find_file_cache(cloth_sim)}:{find_file_cache(hair_sim)}"
        io_message = ''
        add_index_check(_node)
        if _node.node('check_wrap').errors() or _node.node('check_wrap1').errors():
            return "布料或者毛发的生长面点序没有对齐或者缺少index属性！"
        if _node.node('check_wrap2').errors() or _node.node('check_wrap3').errors():
            return "布料或者毛发的生长面面序号没有对齐或者缺少pindex属性！"
        for i in find_vellum_io(cloth_sim) + find_vellum_io(hair_sim):
            io_node: hou.SopNode = i
            logger.info(io_node)
            if io_node.parm('filemethod').eval() == 0:
                io_message += f'io节点{io_node.name()}在发布前应该把filepath类型改为explicit\n'
        if io_message:
            return io_message

        check_import = check_unknown_import(_node)
        if check_import:
            return check_import


        compmessage = compare_nodes(hair_in, hair_out, True)
        compmessage += compare_nodes(mesh_in, mesh_out)
        if not check_cloth_sim(cloth_sim):
            compmessage += compare_nodes(high_sim, wrap_ok)
        return compmessage

    except Exception:
        return traceback.format_exc()




