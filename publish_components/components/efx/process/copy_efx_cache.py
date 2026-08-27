import os
import shutil
import traceback
from oct_hou.utils import efx_node_utils
from pxr import Usd
import hou
from oct.pipeline.path_acs import unlock_path, lock_path, make_dirs, remove



def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
复制efx cache 文件且生成入口文件到i盘
    """
    try:

        def gener_comp_usd(tar_usd, ref_usd, comp_name):
            stage = Usd.Stage.CreateNew(tar_usd)
            d_prim = stage.DefinePrim(f'/{comp_name}', 'Xform')
            stage.SetDefaultPrim(d_prim)
            d_prim.GetReferences().AddReference(os.path.relpath(ref_usd, os.path.dirname(tar_usd)), f'/{comp_name}')
            stage.Save()

        dst_hou_file = process_data['version_dir'] + '/' + os.path.basename(hou.hipFile.path())
        shutil.copyfile(hou.hipFile.path(), dst_hou_file)
        process_data['geo_file'] = dst_hou_file


        v_comp_dir = process_data['version_dir'] + '/components'
        if os.path.exists(v_comp_dir):
            remove(v_comp_dir)

        while os.path.exists(v_comp_dir):
            if not os.path.exists(v_comp_dir):
                break
        make_dirs(v_comp_dir)
        unlock_path(v_comp_dir, True)
        for k,v in submit_data['components'].items():
            comp_path = v_comp_dir+f'/{k}'
            if not os.path.exists(comp_path):
                make_dirs(comp_path)
            comp_node = v['cache_node']
            comp_type = v['cache_type']
            if comp_type == "禁用":
                continue
            is_seq = False
            if 'oct_export_usd_vdb' in comp_node.type().name():
                cache_file_parm = comp_node.parm('file')
                is_seq = True
            else:
                cache_file_parm = comp_node.parm('lopoutput')
                if comp_node.parm('export_seq').eval():
                    is_seq = True

            if not is_seq:
                dst_file = f"{comp_path}/{os.path.basename(cache_file_parm.eval())}"
                shutil.copy(cache_file_parm.eval(), dst_file)
                comp_usd = f"{comp_path}/comp.usda"
                gener_comp_usd(comp_usd, dst_file, k)
            else:
                file = cache_file_parm.eval()
                file_folder = os.path.dirname(file)
                dst_file = f"{comp_path}/{os.path.basename(file_folder)}"
                shutil.copytree(file_folder, dst_file)
                if comp_node.type().name() == "huiwentong::oct_export_usd_instance":
                    efx_node_utils.oct_export_usd_instance_on_seq_gen(comp_node, dst_file, f'{comp_path}/{k}.usda')
                    gener_comp_usd(f'{comp_path}/comp.usda', f'{comp_path}/{k}.usda', k)
                elif comp_node.type().name() == "huiwentong::oct_export_usd_vdb":
                    efx_node_utils.oct_export_usd_vdb_on_gen(comp_node, dst_file, f'{comp_path}/comp.usda')
                elif comp_node.type().name() == "huiwentong::oct_export_usd":
                    efx_node_utils.oct_export_usd_on_seq_gen(comp_node, dst_file, f'{comp_path}/{k}.usda')
                    gener_comp_usd(f'{comp_path}/comp.usda', f'{comp_path}/{k}.usda', k)
                elif comp_node.type().name() == "huiwentong::oct_export_usd_broken":
                    efx_node_utils.oct_export_usd_broken_on_seq_gen(comp_node, dst_file, f'{comp_path}/{k}.usda')
                    gener_comp_usd(f'{comp_path}/comp.usda', f'{comp_path}/{k}.usda', k)
    except:
        return traceback.format_exc()



