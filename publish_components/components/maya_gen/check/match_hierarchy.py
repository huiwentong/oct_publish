# -*- coding: utf-8 -*-
import os
import importlib
import traceback
import pymel.core as pm
import maya.cmds as cmds
from publish_components.utils.maya_utils import mod_diff
from oct.pipeline.task_context import TaskContext
importlib.reload(mod_diff)

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    与模型版本对比层级、拓扑变化。
    """

    def get_last_version(mod_v, mod_p):
        """
        根据 modelPath 查找对应模型版本的 mesh.xml。
        """
        version_root = os.path.dirname(os.path.dirname(mod_p))
        version_dir_name = os.path.basename(os.path.dirname(mod_p))
        mesh_xml = None
        tokens = version_dir_name.split('.')
        is_version_dir = (len(tokens) == 4 and tokens[-1].startswith('v') and tokens[-1][1:].isdigit())

        if is_version_dir:
            version_key = '.'.join(tokens[:3])
            for dir_name in sorted(os.listdir(version_root)):
                xml_path = os.path.join(version_root, dir_name, 'mesh.xml')
                if dir_name.startswith(version_key + '.v') and dir_name[-3:].isdigit() and os.path.isfile(xml_path):
                    mesh_xml = xml_path
                    mod_v = dir_name[-3:]

        else:
            xml_path = os.path.join(os.path.dirname(mod_p), 'mesh.xml')
            if os.path.isfile(xml_path):
                mesh_xml = xml_path

        return mod_v, mesh_xml

    def build_error_message(items, title, limit=5, separator=' '):
        """
        统一生成 mesh 差异信息。
        """
        if not items:
            return u''
        msg = u'\n有 {} {}'.format(len(items), title)
        if len(items) > limit:
            msg += separator.join(items[:limit]) + u' ...'
        else:
            msg += separator.join(items)
        return msg

    try:
        result = None
        can_continue = True
        task_id = process_data["task_id"]
        tc = TaskContext(task_id) or TaskContext.from_env()
        step_name = tc.step_name.lower()
        sg_asset_type = tc.entity.sg_asset_type
        version_dir = process_data["version_dir"]
        n_root = process_data.get("root", '|Root_grp')
        n_root = pm.PyNode(n_root)

        mesh_xml = None
        mod_version = None
        desp = u''
        md_msg = u''

        # MOD
        if step_name == 'mod':
            attrs = ['modelVersion', 'modelPath', 'modVersion', 'modPath', 'textureVersion', 'texturePath',]
            for attr in attrs:
                attr_name = '{}.{}'.format(str(n_root), attr)
                if cmds.objExists(attr_name):
                    cmds.deleteAttr(attr_name)

            desp = u"和上一个 Publish 版本模型相比"
            version_dir_no_num = process_data["version_dir_no_num"]
            mesh_xml = os.path.join(version_dir_no_num, 'mesh.xml' )
            if not os.path.isfile(mesh_xml):
                result = u''
                can_continue = False

        else:
            root_attrs = pm.listAttr(n_root) or []

            if 'modelVersion' in root_attrs and 'modelPath' in root_attrs:
                mod_version = n_root.getAttr('modelVersion')
                mod_path = n_root.getAttr('modelPath')

                if mod_path and mod_path.startswith('I:'):
                    mod_path = mod_path.replace('I:', 'i:', 1)
                    n_root.setAttr('modelPath', mod_path)

                if mod_path:
                    mod_path = mod_path.replace("\\", "/")
                asset_dir = os.path.dirname(os.path.dirname(version_dir))
                if mod_path and not mod_path.startswith(asset_dir):
                    result = u"Root_grp 的 modelPath 属性值为{0} 不匹配当前资产.".format(mod_path)
                    can_continue = False

                if can_continue and mod_path and os.path.isdir(os.path.dirname(mod_path)):
                    mod_version, mesh_xml = get_last_version(mod_version, mod_path)

            if can_continue and not mesh_xml:
                asset_dir = os.path.dirname(os.path.dirname(version_dir))
                mod_dir = os.path.join(asset_dir, 'mod')

                if os.path.isdir(mod_dir):

                    for version_name in sorted(os.listdir(mod_dir)):
                        if len(version_name.split('.')) != 4:
                            continue
                        xml_path = os.path.join( mod_dir, version_name, 'mesh.xml')
                        if not os.path.isfile(xml_path):
                            continue

                        if mesh_xml and '.H_MOD.' in mesh_xml and '.H_MOD.' not in version_name:
                            continue

                        mesh_xml = xml_path
                        mod_version = version_name[-3:]

                if not mesh_xml:
                    result = u"没有找到模型对应的 xml 文件"
                    can_continue = False

            if can_continue:
                desp = u"和模型 V{} 相比".format(mod_version)

        if can_continue and step_name != 'mod':
            root_attrs = pm.listAttr(n_root) or []
            if 'modelVersion' not in root_attrs:
                pm.addAttr(n_root, shortName='modelv', longName='modelVersion', dt='string')
            if 'modelPath' not in root_attrs:
                pm.addAttr(n_root, shortName='modelp', longName='modelPath', dt='string')

            n_root.setAttr('modelVersion', mod_version)
            current_model_path = n_root.getAttr('modelPath')
            mesh_xml_dir = os.path.dirname(mesh_xml)
            if not (current_model_path and current_model_path.startswith(mesh_xml_dir)):
                n_root.setAttr('modelPath', mesh_xml)

        if can_continue:
            md = mod_diff.Mod_Diff()
            n_high = process_data.get("high", "|Root_grp|Geo_grp|high")
            n_high = pm.PyNode(n_high)
            md.parse_xml(mesh_xml, n_high.fullPath())

            err_missing = u''
            err_new = u''
            err_moved = u''
            err_topology_changed = u''
            err_vtx_num = u''
            err_wrong_order = u''

            if md.l_missing:
                err_missing = build_error_message(md.l_missing,u"个mesh被删除了:\n")

                if step_name == 'tex' and sg_asset_type == 'CH':
                    logger.warning(err_missing)
                else:
                    md_msg += err_missing

            if md.l_new:
                err_new = build_error_message(md.l_new, u"个mesh被创建了: ")
                md_msg += err_new

            if md.l_moved:
                err_moved = build_error_message(md.l_moved,u"个mesh被改变了层级: ")
                md_msg += err_moved

            if md.l_topology_changed:
                err_topology_changed = build_error_message(md.l_topology_changed, u"个mesh被改变了拓扑: ")
                md_msg += err_topology_changed

            if md.l_vtx_num:
                err_vtx_num = build_error_message(md.l_vtx_num,
                                                  u"个mesh 点数不一致（可以用 Maya > Mesh > Cleanup > 'Invalid Component' 清理）: ")
                md_msg += err_vtx_num

            if md.l_wrong_order:
                err_wrong_order = u'\n有 {} 个mesh顺序不一样'.format(len(md.l_wrong_order))
                err_wrong_order += u''.join(md.l_wrong_order)
                md_msg += err_wrong_order

            # MOD Publish
            if step_name == 'mod':
                auto_descriptions = {}
                if not err_missing and not err_new and not err_moved and not err_topology_changed:
                    description = u" 本版本无层级拓扑变化。"
                    auto_descriptions[desp] = description
                    md_msg += desp + description
                else:
                    description = (err_missing + err_new + err_moved + err_topology_changed + err_vtx_num)
                    description = description.replace('Shape','')
                    auto_descriptions[desp] = description
                process_data.update({"auto_description": auto_descriptions})

            else:
                has_err = False
                if md.l_missing:
                    if step_name != 'tex' or sg_asset_type != 'CH':
                        desp += err_missing
                        has_err = True

                if md.l_new:
                    desp += err_new
                    has_err = True

                if md.l_moved:
                    desp += err_moved
                    has_err = True

                if md.l_topology_changed:
                    desp += err_topology_changed
                    has_err = True

                if md.l_vtx_num:
                    desp += err_vtx_num
                    has_err = True

                if md.l_wrong_order:
                    desp += err_wrong_order
                    has_err = True

                if has_err:
                    result = desp
        if result:
            return result

    except Exception:
        return traceback.format_exc()
