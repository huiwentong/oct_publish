import traceback
from pprint import pprint
from publish_core.database.entity import SGEntity
import hou
import os
from pxr import Usd,Gf,Sdf


def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
检查缓存或VDB 是否存在且合法。
    """
    def check_node(check_node:hou.SopNode, comp_name):
        if check_node is None:
            return f"存在未指定输出节点的component！{comp_name}"
        if check_node.type().name() != 'huiwentong::oct_export_usd_broken':
            if check_node.parm('comp_name').eval() != comp_name:
                return f"输出节点{comp_name}的comp名字和comp节点不一致"
        else:
            if check_node.parm('broken_name').eval() != comp_name:
                return f"输出节点{comp_name}的comp名字和comp节点不一致"
        return None

    def check_cache_exist(check_node:hou.SopNode):
        comp_name = check_node.parm('comp_name').eval()
        start_frame = hou.playbar.frameRange()[0]
        end_frame = hou.playbar.frameRange()[1]
        is_seq = False

        if 'oct_export_usd_vdb' in check_node.type().name():
            cache_file_parm = check_node.parm('file')
            if check_node.parm('export_seq').eval():
                is_seq = True
        else:
            cache_file_parm = check_node.parm('lopoutput')
            if check_node.parm('export_seq').eval():
                is_seq = True

        if not is_seq:
            file = cache_file_parm.eval()
            if not os.path.exists(file):
                return f"component： {comp_name}的缓存不存在！"
        else:
            for frame in range(int(start_frame), int(end_frame)):
                file = cache_file_parm.evalAtFrame(frame)
                if not os.path.exists(file):
                    return f"component： {comp_name}的缓存，在第{frame}帧没有找到对应的文件"

        return None


    def check_cache_hierarchy(check_node:hou.SopNode):
        comp_name = check_node.parm('comp_name').eval()
        if 'oct_export_usd_vdb' in check_node.type().name():
            return None
        cache_file = check_node.parm('lopoutput').evalAtFrame(hou.playbar.frameRange()[0])
        stage = Usd.Stage.Open(cache_file)
        if check_node.type().name() == 'huiwentong::oct_export_usd_broken':
            comp_name = check_node.parm('broken_name').eval()
            prim = stage.GetPrimAtPath(f'/{comp_name}/high/body')
        else:
            prim = stage.GetPrimAtPath(f'/{comp_name}/efx_gen')
        if not prim:
            print(cache_file)
            print(prim)
            print(f'/{comp_name}/efx_gen')
            return f"component：{comp_name}的缓存文件中没有找到层级： /{comp_name}/efx_gen"

    
    try:
        l_invalid_src = []
        for k, v in submit_data:
            comp_name = k
            comp_node = v['cache_node']
            comp_type = v['cache_type']
            logger.info(comp_name, comp_type, comp_node)
            if comp_type == "禁用":
                continue
            node_check = check_node(comp_node, comp_name)
            if node_check:
                l_invalid_src.append(node_check)
                continue
            cache_ex_check = check_cache_exist(comp_node)
            if cache_ex_check:
                l_invalid_src.append(cache_ex_check)
                continue

            hiera_check = check_cache_hierarchy(comp_node)
            if hiera_check:
                l_invalid_src.append(hiera_check)
                continue
        if l_invalid_src:
            return u"文件不存在\n  " + '\n  '.join(l_invalid_src)
    except:
        return traceback.format_exc()