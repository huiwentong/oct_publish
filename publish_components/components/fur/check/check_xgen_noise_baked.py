# -*- coding: utf-8 -*-
import traceback
import maya.mel as mel
import xgenm as xg

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """检查 XGen Noise Modifier 是否已烘焙。"""
    try:
        def collect_unbaked(palette,descriptions):
            unbaked={}
            for description in descriptions:
                modifiers=xg.fxModules(str(palette),str(description)) or []
                for modifier in modifiers:
                    if xg.fxModuleType(str(palette),str(description),str(modifier))!="NoiseFXModule":
                        continue
                    mode=xg.getAttr("mode",str(palette),str(description),str(modifier))
                    if str(mode)=="0":
                        unbaked.setdefault(description,[]).append(modifier)
            return unbaked

        palette=process_data.get("xgen_palette_name")
        descriptions=process_data.get("xgen_descriptions",[])
        if not palette:
            raise RuntimeError(u"没有获取到 XGen Palette 信息")
        if not descriptions:
            raise RuntimeError(u"没有获取到 XGen Description 信息")

        unbaked=collect_unbaked(palette,descriptions)
        process_data["xgen_unbaked_noise"]=unbaked

        if unbaked:
            items=[]
            for description,modifiers in unbaked.items():
                items.extend("{}-{}".format(description,modifier) for modifier in modifiers)
            raise RuntimeError(u"以下 Noise 修改器没有烘焙数据：{}".format(", ".join(items)))

        if logger:
            logger.info(u"XGen Noise Modifier 烘焙检查通过")
    except Exception:
        return traceback.format_exc()

def fix(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """烘焙未完成的 XGen Noise Modifier。"""
    try:
        def collect_unbaked(palette,descriptions):
            unbaked={}
            for description in descriptions:
                modifiers=xg.fxModules(str(palette),str(description)) or []
                for modifier in modifiers:
                    if xg.fxModuleType(str(palette),str(description),str(modifier))!="NoiseFXModule":
                        continue
                    mode=xg.getAttr("mode",str(palette),str(description),str(modifier))
                    if str(mode)=="0":
                        unbaked.setdefault(description,[]).append(modifier)
            return unbaked

        palette=process_data.get("xgen_palette_name")
        descriptions=process_data.get("xgen_descriptions",[])
        if not palette:
            raise RuntimeError(u"没有获取到 XGen Palette 信息")
        if not descriptions:
            raise RuntimeError(u"没有获取到 XGen Description 信息")

        unbaked=process_data.get("xgen_unbaked_noise")
        if unbaked is None:
            unbaked=collect_unbaked(palette,descriptions)

        if unbaked:
            errors=[]
            for description,modifiers in unbaked.items():
                try:
                    if logger:
                        logger.info(u'开始烘焙 "{}"：{}'.format(description,", ".join(modifiers)))

                    for modifier in modifiers:
                        xg.setAttr("mode","2",str(palette),str(description),str(modifier))

                    mel.eval('xgmNullRender -pb "{}"'.format(description))

                    for modifier in modifiers:
                        xg.setAttr("mode","1",str(palette),str(description),str(modifier))

                    if logger:
                        logger.info(u"Noise 烘焙完成：{}".format(description))
                except Exception:
                    errors.append(description)
                    for modifier in modifiers:
                        try:
                            xg.setAttr("mode","0",str(palette),str(description),str(modifier))
                        except Exception:
                            pass

            if errors:
                raise RuntimeError(u"以下 Description 的 Noise 烘焙失败：{}".format(", ".join(errors)))

            process_data["xgen_unbaked_noise"]={}

        if logger:
            logger.info(u"XGen Noise Modifier 修复完成")
    except Exception:
        return traceback.format_exc()