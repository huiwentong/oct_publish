# -*- coding: utf-8 -*-
import traceback
import maya.mel as mel

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """检查场景中 XGen Palette 数量是否为一个，并缓存 Palette 信息。"""
    try:
        palettes=mel.eval('ls -long -type "xgmPalette";') or []
        if isinstance(palettes,str):
            palettes=[palettes]

        if not palettes:
            raise RuntimeError(u"场景中没有找到 XGen Palette")
        if len(palettes)>1:
            raise RuntimeError(u"场景中存在多个 XGen Palette，请检查：\n{}".format("\n".join(palettes)))

        palette_node=str(palettes[0])
        palette_name=palette_node.rsplit("|",1)[-1]

        process_data["xgen_palette_node"]=palette_node
        process_data["xgen_palette_name"]=palette_name

        if logger:
            logger.info(u"XGen Palette：{}".format(palette_name))
    except Exception:
        return traceback.format_exc()