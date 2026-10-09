# -*- coding: utf-8 -*-
import traceback
import maya.cmds as cmds
import maya.utils as utils


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查模型层级上值为空的 USD_typeName 属性"""
    # 导出 usd 时 USD_typeName 会覆写 prim 的 typeName，值为空就导出无类型 prim。
    # Houdini usdimport 遍历到无类型 prim 会中断，自动减面拿不到几何，写出空的 low.usd。
    try:
        def check():
            root = process_data.get("geo", "|Root_grp|Geo_grp")
            if not cmds.objExists(root):
                return None
            nodes = [root] + (cmds.listRelatives(root, allDescendents=True, fullPath=True) or [])
            empty_attrs = []
            for node in nodes:
                plug = node + '.USD_typeName'
                if (cmds.objExists(plug)
                        and cmds.getAttr(plug, type=True) == 'string'
                        and cmds.getAttr(plug) in (None, '')):
                    empty_attrs.append(plug)
            return sorted(set(empty_attrs))

        empty_attrs = utils.executeInMainThreadWithResult(check)
        if empty_attrs is None:
            return u"找不到模型导出根节点 {0}".format(process_data.get("geo", "|Root_grp|Geo_grp"))
        if empty_attrs:
            process_data["empty_usd_type_name_attrs"] = empty_attrs
            return u"以下空 USD_typeName 属性会导致 USD 导出类型为空，请自动修复后重新检查：\n" + '\n'.join(empty_attrs)

    except Exception:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """删除值为空的 USD_typeName 属性，非空类型保留"""
    try:
        def repair():
            errors = []
            cmds.undoInfo(openChunk=True, chunkName='fix_empty_usd_type_name')
            try:
                for plug in process_data.get("empty_usd_type_name_attrs", []):
                    if not cmds.objExists(plug):
                        continue
                    node = plug.rsplit('.', 1)[0]
                    was_locked = bool(cmds.getAttr(plug, lock=True))
                    try:
                        # 节点本身被锁时无法删除其属性，需先解除节点锁再解属性锁
                        cmds.lockNode(node, lock=False, lockUnpublished=False)
                        if was_locked:
                            cmds.setAttr(plug, lock=False)
                        cmds.deleteAttr(plug)
                        logger.warning(u"AUTO FIX: 删除空 USD_typeName 属性: {0}".format(plug))
                    except Exception as error:
                        errors.append(u'{0}: {1}'.format(plug, error))
                        if was_locked and cmds.objExists(plug):
                            try:
                                cmds.setAttr(plug, lock=True)
                            except Exception as lock_error:
                                errors.append(u'恢复属性锁定失败 {0}: {1}'.format(plug, lock_error))
            finally:
                cmds.undoInfo(closeChunk=True)
            return errors

        errors = utils.executeInMainThreadWithResult(repair)
        if errors:
            return u"以下属性无法自动删除，请手动处理后重新检查：\n" + '\n'.join(errors)

    except Exception:
        return traceback.format_exc()
