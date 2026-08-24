import os
import glob
import traceback
import shutil
import pymel.core as pm
from publish_components.utils.maya_utils import get_upstream_nodes
def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """拷贝资产的贴图到 I: 版本文件夹"""

    try:

        def get_asset_tex_node():
            asset_tex_node = []
            d_se_info = {}
            n_root = process_data.get('root', '|Root_grp')
            n_root = pm.PyNode(n_root)
            for se in pm.ls(type='shadingEngine'):
                d_se_info[se.nodeName()] = {'tex': [], 'nodes': []}
                for node_path in get_upstream_nodes.get_nodes(se):
                    _node = pm.PyNode(node_path)
                    if _node.nodeType() in ['file', 'aiImage']:
                        d_se_info[se.nodeName()]['tex'].append(_node)
                    d_se_info[se.nodeName()]['nodes'].append(node_path)

            for se, se_info in d_se_info.items():
                for node_path in se_info['nodes']:
                    if node_path.startswith(n_root.fullPath() + '|'):
                        asset_tex_node.extend(se_info['tex'])
                        break
            return asset_tex_node


        v_dir_imgs = process_data["v_dir_imgs"]
        if not os.path.isdir(v_dir_imgs):
            os.makedirs(v_dir_imgs)

        for n in get_asset_tex_node():
            seq_v = False
            if n.type() == 'file':
                attr = n.computedFileTextureNamePattern
                seq_attr = n.useFrameExtension
                if seq_attr.get():
                    seq_v = True
            elif n.type() == 'aiImage':
                attr = n.filename
            else:
                continue

            img_path = attr.get()

            if not seq_v:
                if os.path.isfile(img_path):
                    dst = v_dir_imgs + '/' + os.path.basename(img_path)
                    shutil.copyfile(img_path, dst)
            else:
                img_path = pm.getAttr(n.name() + '.computedFileTextureNamePattern')
                matched_file_list = glob.glob(img_path.replace('<f>', '*'))
                matched_file_list = [path.replace('\\', '/') for path in matched_file_list]
                for file_path in matched_file_list:
                    dst = v_dir_imgs + '/' + os.path.basename(file_path)
                    if file_path.replace('\\', '/') != dst:
                        shutil.copyfile(file_path.replace('\\', '/'), dst)

    except Exception:
        return traceback.format_exc()
