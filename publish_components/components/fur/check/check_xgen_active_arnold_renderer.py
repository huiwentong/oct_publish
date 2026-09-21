# -*- coding: utf-8 -*-
import traceback
import xgenm as xg
import xgenm.xgGlobal as xgg

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """检查 XGen Description 是否启用 Arnold Renderer。"""
    try:
        def get_invalid_descriptions(palette,descriptions):
            invalid=[]
            for description in descriptions:
                active_renderer=xg.getActive(str(palette),str(description),"Renderer")
                renderer=xg.getAttr("renderer",str(palette),str(description),"RendermanRenderer")
                if active_renderer!="RendermanRenderer" or renderer!="Arnold Renderer":
                    invalid.append(description)
            return invalid

        palette=process_data.get("xgen_palette_name")
        descriptions=process_data.get("xgen_descriptions",[])
        if not palette:
            raise RuntimeError(u"没有获取到 XGen Palette 信息")
        if not descriptions:
            raise RuntimeError(u"没有获取到 XGen Description 信息")

        invalid=get_invalid_descriptions(palette,descriptions)
        if invalid:
            raise RuntimeError(u"以下 Description 未正确启用 Arnold Renderer：\n{}".format("\n".join(invalid)))

        if logger:
            logger.info(u"XGen Arnold Renderer 检查通过")
    except Exception:
        return traceback.format_exc()

def fix(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """自动将 XGen Description Renderer 设置为 Arnold Renderer。"""
    try:
        def get_invalid_descriptions(palette,descriptions):
            invalid=[]
            for description in descriptions:
                active_renderer=xg.getActive(str(palette),str(description),"Renderer")
                renderer=xg.getAttr("renderer",str(palette),str(description),"RendermanRenderer")
                if active_renderer!="RendermanRenderer" or renderer!="Arnold Renderer":
                    invalid.append(description)
            return invalid

        def refresh_xgen():
            editor=getattr(xgg,"DescriptionEditor",None)
            if editor:
                try:
                    editor.refresh("Full")
                except Exception:
                    pass

        palette=process_data.get("xgen_palette_name")
        descriptions=process_data.get("xgen_descriptions",[])
        if not palette:
            raise RuntimeError(u"没有获取到 XGen Palette 信息")
        if not descriptions:
            raise RuntimeError(u"没有获取到 XGen Description 信息")

        invalid=get_invalid_descriptions(palette,descriptions)
        if invalid:
            errors=[]
            for description in invalid:
                try:
                    if logger:
                        logger.warning(u'AUTO FIX: 设置 Description "{}" 使用 Arnold Renderer'.format(description))
                    xg.setActive(str(palette),str(description),"RendermanRenderer")
                    xg.setAttr("renderer","Arnold Renderer",str(palette),str(description),"RendermanRenderer")
                except Exception:
                    errors.append(description)

            refresh_xgen()

            if errors:
                raise RuntimeError(u"以下 Description 的 Arnold Renderer 修复失败：{}".format(", ".join(errors)))

            invalid=get_invalid_descriptions(palette,descriptions)
            if invalid:
                raise RuntimeError(u"以下 Description 修复后仍未正确启用 Arnold Renderer：\n{}".format("\n".join(invalid)))

        if logger:
            logger.info(u"XGen Arnold Renderer 修复完成")
    except Exception:
        return traceback.format_exc()