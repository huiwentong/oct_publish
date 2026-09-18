# -*- coding: utf-8 -*-
import traceback
import maya.mel as mel
import xgenm as xg

def _get_maya_palettes():
    nodes=mel.eval('ls -long -type "xgmPalette";') or []
    if isinstance(nodes,str):
        nodes=[nodes]
    return nodes

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """检查 Maya XGen Palette 是否已正确注册到 XGen Core。"""
    try:
        maya_nodes=_get_maya_palettes()
        if not maya_nodes:
            return ""

        maya_palettes=set(str(x).rsplit("|",1)[-1] for x in maya_nodes)
        core_palettes=set(str(x) for x in (xg.palettes() or []))
        missing=maya_palettes-core_palettes

        if missing:
            return (
                u"XGen Core 未加载 Palette：{}\n"
                u"Publisher 已初始化 XGen，请重新打开一次当前 Fur 场景后再次检查。"
            ).format(", ".join(sorted(missing)))

        if logger:
            logger.info(
                u"XGen Core 检查通过：{}".format(
                    ", ".join(sorted(core_palettes))
                )
            )

        return ""
    except Exception:
        return traceback.format_exc()