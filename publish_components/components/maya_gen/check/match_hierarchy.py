# -*- coding: utf-8 -*-
import os
import importlib
import traceback
import pymel.core as pm
import maya.cmds as cmds
from publish_components.utils.maya_utils import mod_diff
from oct.pipeline.task_context import TaskContext
importlib.reload(mod_diff)


def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
    与模型版本对比层级拓扑。
    """
    # 需要重构
    try:
        task_id = process_data["task_id"]
        tc = TaskContext(task_id) or TaskContext.from_env()
        sg_asset_type = tc.entity.sg_asset_type
        def get_last_version(mod_v, m_path):
            v_root = os.path.dirname(os.path.dirname(m_path))
            v_dir_name = os.path.basename(os.path.dirname(m_path))
            _xml = None
            tokens = v_dir_name.split('.')
            if len(tokens) == 4 and tokens[-1][0] == 'v' and tokens[-1][1:].isdigit():
                v_key = '.'.join(tokens[:3])
                for dir_name in sorted(os.listdir(v_root)):
                    if dir_name.startswith(v_key + '.v') and dir_name[-3:].isdigit() and os.path.isfile(
                            '{}/{}/mesh.xml'.format(v_root, dir_name)):
                        _xml = '{}/{}/mesh.xml'.format(v_root, dir_name)
                        mod_v = dir_name[-3:]

                return mod_v, _xml
            else:
                if os.path.isfile(os.path.dirname(m_path) + '/mesh.xml'):
                    return mod_v, os.path.dirname(m_path) + '/mesh.xml'
                else:
                    return mod_v, _xml

        md_msg = ''
        step_name = tc.step_name.lower()
        n_root = process_data.get("root", pm.PyNode('|Root_grp'))
        n_root = pm.PyNode(n_root)
        logger.info("root_node: {}".format(n_root))
        version_dir = process_data["version_dir"]

        if step_name == 'mod':
            attrs = ['modelVersion', 'modelPath', 'modVersion', 'modPath', 'textureVersion', 'texturePath']
            for attr in attrs:
                if cmds.objExists(n_root + '.' + attr):
                    cmds.deleteAttr(n_root + '.' + attr)
            desp = u"和上一个 Publish 版本模型相比"
            version_dir_no_num = process_data["version_dir_no_num"]
            mesh_xml = version_dir_no_num + '/mesh.xml'
            if not os.path.isfile(mesh_xml):
                return ""

        else:
            l_attrs = pm.listAttr(n_root)
            if 'modelVersion' in l_attrs and 'modelPath' in l_attrs:
                mod_version = n_root.getAttr('modelVersion')
                mod_path = n_root.getAttr('modelPath')
                if mod_path.startswith('I:'):
                    n_root.setAttr('modelPath', mod_path.replace('I:', 'i:'))
                    mod_path = n_root.getAttr('modelPath')
                asset_dir = os.path.dirname(os.path.dirname(version_dir))
                mod_path = mod_path.replace("\\", "/")
                if not mod_path.startswith(asset_dir):
                    return u"Root_grp 的 modelPath 属性值为{0} 不匹配当前资产.".format(mod_path)

                if mod_path and os.path.isdir(os.path.dirname(mod_path)):
                    mod_version, mesh_xml = get_last_version(mod_version, mod_path)

            if not mesh_xml:
                asset_dir = os.path.dirname(os.path.dirname(version_dir))
                if os.path.isdir(asset_dir + '/mod'):
                    for v_name in sorted(os.listdir(asset_dir + '/mod')):
                        if len(v_name.split('.')) != 4:
                            continue
                        if os.path.isfile(asset_dir + '/mod/' + v_name + '/mesh.xml'):
                            if mesh_xml and '.H_MOD.' in mesh_xml and not '.H_MOD.' in v_name:
                                continue
                            mesh_xml = asset_dir + '/mod/' + v_name + '/mesh.xml'
                            mod_version = v_name[-3:]
                if not mesh_xml:
                    return u"没有找到模型对应的 xml 文件"

            desp = u"和模型 V{} 相比".format(mod_version)

        if step_name != 'mod':
            l_attrs = pm.listAttr(n_root)
            if not 'modelVersion' in l_attrs:
                pm.addAttr(n_root, shortName='modelv', longName='modelVersion', dt="string")
            n_root.setAttr('modelVersion', mod_version)

            if not 'modelPath' in l_attrs:
                pm.addAttr(n_root, shortName='modelp', longName='modelPath', dt="string")
            if not (n_root.getAttr('modelPath') and n_root.getAttr('modelPath').startswith(
                    os.path.dirname(mesh_xml))):
                n_root.setAttr('modelPath', mesh_xml)

        md = mod_diff.Mod_Diff()
        n_high = process_data["high"]
        md.parse_xml(mesh_xml, n_high.fullPath())

        err_missing = u''
        err_new = u''
        err_moved = u''
        err_topology_changed = u''
        err_vtx_num = u''
        err_wrong_order = u''

        if len(md.l_missing) != 0:
            err_missing += u'\n有 ' + str(len(md.l_missing)) + u" 个mesh被删除了:\n"
            if len(md.l_missing) > 5:
                err_missing += u' '.join(md.l_missing[:5]) + u" ..."
            else:
                err_missing += u' '.join(md.l_missing)

            if step_name == 'tex' and sg_asset_type == 'CH':
                logger.warning(err_missing)
            else:
                md_msg += err_missing

        if len(md.l_new) != 0:
            err_new += u'\n有 ' + str(len(md.l_new)) + u" 个mesh被创建了: "
            if len(md.l_new) > 5:
                err_new += u' '.join(md.l_new[:5]) + u" ..."
            else:
                err_new += u' '.join(md.l_new)
            md_msg += err_new

        if len(md.l_moved) != 0:
            err_moved += u'\n有 ' + str(len(md.l_moved)) + u" 个mesh被改变了层级: "
            if len(md.l_moved) > 5:
                err_moved += u' '.join(md.l_moved[:5]) + u" ..."
            else:
                err_moved += u' '.join(md.l_moved)
            md_msg += err_moved

        if len(md.l_topology_changed) != 0:
            err_topology_changed += u'\n有 ' + str(len(md.l_topology_changed)) + u" 个mesh被改变了拓扑: "
            if len(md.l_topology_changed) > 5:
                err_topology_changed += u' '.join(md.l_topology_changed[:5]) + u" ..."
            else:
                err_topology_changed += u' '.join(md.l_topology_changed)
            md_msg += err_topology_changed

        if len(md.l_vtx_num) != 0:
            err_vtx_num += u'\n有 ' + str(
                len(md.l_vtx_num)) + u" 个mesh 点数不一致（可以用 Maya > Mesh > Cleanup > 'Invalid Component' 清理）: "
            if len(md.l_moved) > 5:
                err_vtx_num += u' '.join(md.l_vtx_num[:5]) + u" ..."
            else:
                err_vtx_num += u' '.join(md.l_vtx_num)
            md_msg += err_vtx_num

        if len(md.l_wrong_order) > 0:
            err_wrong_order += u'\n有 ' + str(len(md.l_wrong_order)) + u" 个mesh顺序不一样: "
            err_wrong_order += u''.join(md.l_wrong_order)
            md_msg += err_wrong_order

        # Fill the description field for mod publish

        if step_name == 'mod':
            d_auto_descriptions = {}
            if err_missing == u'' and err_new == u'' and err_moved == u'' and err_topology_changed == u'':
                d_auto_descriptions[desp] = u" 本版本无层级拓扑变化。"
                md_msg += desp + u" 本版本无层级拓扑变化。"
            else:
                msg = err_missing + err_new + err_moved + err_topology_changed + err_vtx_num
                msg = msg.replace('Shape', '')
                d_auto_descriptions[desp] = msg
            process_data.update({"auto_description": d_auto_descriptions})

        # The order of errors: missing > new > moved > topology changed
        else:
            has_err = False
            if len(md.l_missing) > 0:
                if step_name != 'tex' or sg_asset_type!= 'CH':
                    desp += err_missing
                    has_err = True

            if len(md.l_new) > 0:
                desp += err_new
                has_err = True

            if len(md.l_moved) > 0:
                desp += err_moved
                has_err = True

            if len(md.l_topology_changed) > 0:
                desp += err_topology_changed
                has_err = True

            if len(md.l_vtx_num) > 0:
                desp += err_vtx_num
                has_err = True

            if len(md.l_wrong_order) > 0:
                desp += err_wrong_order
                has_err = True

            if has_err:
                return desp
    except:
        return traceback.format_exc()


