# -*- coding: utf-8 -*-
import traceback
import maya.cmds as cmds

def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
    检查模型是否带有colorset
    """
    try:
        def get_meshes_with_colorset():
            result = []
            meshes = cmds.ls(type='mesh', long=True)

            for m in meshes:
                # 查询该 mesh 的 color sets
                color_sets = cmds.polyColorSet(m, query=True, allColorSets=True)
                if color_sets:
                    result.append(m)

            return list(set(result))

        check_result = get_meshes_with_colorset()
        if check_result:
            text = u'以下模型带有colorset: \n{}'.format('\n'.join(list(set(check_result))))
            process_data["check_mod_color_set_error_nodes"] = check_result
            return text
    except:
        return traceback.format_exc()

def fix(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    try:
        def delete_all_colorsets(mesh):
            color_sets = cmds.polyColorSet(mesh, q=True, allColorSets=True) or []
            for cs in color_sets:
                cmds.polyColorSet(mesh, delete=True, colorSet=cs)

        check_result = process_data.get("check_mod_color_set_error_nodes", [])
        if check_result:
            for e_mesh in check_result:
                logger.warning("AUTO FIX: 开始删除 ‘{}’ 的 colorset".format(e_mesh))
                delete_all_colorsets(e_mesh)
    except:
        return traceback.format_exc()


