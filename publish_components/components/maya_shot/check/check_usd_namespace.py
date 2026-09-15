# -*- coding: utf-8 -*-
import re
import traceback

import maya.cmds as cmds
import maya.utils as utils


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    检查 usd 流程的 namespace：AR_ 组名、引用 namespace、Geo_grp.usd_path 三者要一致
    """
    # 老 proj_mk2_gen/check_usd_namespace：
    #   |World|asset|<type>|AR_<ns>|<ns>:Root_grp，AR_ 组名去掉 AR_ 要等于子节点 namespace，
    #   <ns>:Geo_grp.usd_path 的末段也要等于 namespace；引用的 namespace 要以资产名开头。
    try:
        def check():
            if not cmds.objExists('|World'):
                return u"当前文件没有 World 组"
            l_errs = []
            if cmds.objExists('|World|asset'):
                for grp in cmds.listRelatives('|World|asset', c=True) or []:
                    if grp == 'asb':
                        continue
                    for ar_grp in cmds.listRelatives(grp, c=True) or []:
                        ar_ns = ar_grp.replace('AR_', '')
                        childs = cmds.listRelatives(ar_grp, c=True)
                        if not childs:
                            l_errs.append(u'{0} 空组请删除'.format(ar_grp))
                            continue
                        child_ns = childs[0].split(':')[0]
                        if ar_ns != child_ns and ar_grp not in l_errs:
                            l_errs.append(ar_grp)
                        usd_path = cmds.getAttr(child_ns + ':Geo_grp.usd_path')
                        if usd_path.split('/')[-1] != child_ns and ar_grp not in l_errs:
                            l_errs.append(ar_grp)

            for ref in cmds.file(q=True, r=True) or []:
                rfn = cmds.file(ref, q=True, rfn=True)
                if cmds.file(rfn=rfn, q=True, deferReference=True):
                    continue
                ns = cmds.file(ref, q=True, ns=True)
                asset_name = ref.split('/')[-1].split('.')[0]
                if not re.match(r'{0}\d*$'.format(re.escape(asset_name)), ns):
                    ar_node = cmds.listRelatives(ns + ':Root_grp', p=True)[0]
                    if ar_node not in l_errs:
                        l_errs.append(ar_node)

            if l_errs:
                return u"当前文件中存在错误 namespace 的情况，请点击 Fix 或用资产管理器纠错：\n" + '\n'.join(l_errs)
            return ""

        result = utils.executeInMainThreadWithResult(check)
        if result:
            return result
    except:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """删除空的 AR_ 组；按 Geo_grp.usd_path 纠正引用 namespace 和 AR_ 组名"""
    try:
        def repair():
            if not cmds.objExists('|World|asset'):
                return u"当前文件没有 |World|asset 组，无法修复"

            l_errs = []
            for grp in cmds.listRelatives('|World|asset', c=True) or []:
                if grp == 'asb':
                    continue
                for ar_grp in cmds.listRelatives(grp, c=True) or []:
                    ar_ns = ar_grp.replace('AR_', '')
                    childs = cmds.listRelatives(ar_grp, c=True)
                    if not childs:
                        logger.info(u'AUTO FIX: 删除空组 {0}'.format(ar_grp))
                        try:
                            cmds.lockNode(ar_grp, lock=False)
                            cmds.delete(ar_grp)
                        except Exception:
                            l_errs.append(ar_grp)
                        continue
                    child_ns = childs[0].split(':')[0]
                    usd_path = cmds.getAttr(child_ns + ':Geo_grp.usd_path')
                    if ar_ns != child_ns or usd_path.split('/')[-1] != child_ns:
                        if ar_grp not in l_errs:
                            l_errs.append(ar_grp)

            # ref 文件名里的资产名和 usd_path 末段对不上，说明引用的资产本身就错了，这里修不了
            wrong_asset = []
            ns_dic = {}
            for ref in cmds.file(q=True, r=True) or []:
                rfn = cmds.file(ref, q=True, rfn=True)
                if cmds.file(rfn=rfn, q=True, deferReference=True):
                    continue
                ns = cmds.file(ref, q=True, ns=True)
                ns_dic[ns] = ref
                asset_name = ref.split('/')[-1].split('.')[0]
                usd_ns = cmds.getAttr(ns + ':Geo_grp.usd_path').split('/')[-1]
                if not re.match(r'{0}\d*$'.format(re.escape(asset_name)), usd_ns):
                    wrong_asset.append(ns)
            if wrong_asset:
                return u'ref 资产与 usd_path 不符，需要通过资产管理器纠错：{0}'.format(wrong_asset)

            for ar_node in l_errs:
                ar_ns = ar_node.replace('AR_', '')
                childs = cmds.listRelatives(ar_node, c=True)
                if not childs:
                    logger.warning(u'{0} 无法自动处理，请手动修改'.format(ar_node))
                    continue
                child_ns = childs[0].split(':')[0]
                usd_ns = cmds.getAttr(child_ns + ':Geo_grp.usd_path').split('/')[-1]
                if child_ns != usd_ns:
                    if cmds.namespace(exists=usd_ns):
                        if usd_ns in ns_dic:
                            # 目标 namespace 被别的引用占着，先把它挪开
                            cmds.file(ns_dic[usd_ns], e=True, ns=usd_ns + '_tmp')
                        else:
                            cmds.namespace(set=':')
                            cmds.namespace(rm=usd_ns, f=True)
                    cmds.file(ns_dic[child_ns], e=True, ns=usd_ns)
                    logger.info(u'AUTO FIX: namespace {0} -> {1}'.format(child_ns, usd_ns))

                if ar_ns != usd_ns:
                    cmds.lockNode(ar_node, lock=False)
                    new_name = cmds.rename(ar_node, 'AR_{0}'.format(usd_ns))
                    cmds.lockNode(new_name, lock=True)
                    logger.info(u'AUTO FIX: {0} -> {1}'.format(ar_node, new_name))
            return ""

        return utils.executeInMainThreadWithResult(repair)
    except:
        return traceback.format_exc()
