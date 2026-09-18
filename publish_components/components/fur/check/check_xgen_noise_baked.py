# -*- coding: utf-8 -*-

import traceback
import maya.mel as mel
import xgenm as xg


def _collect_unbaked(palette, descriptions):
    """收集未烘焙的 Noise Modifier。"""
    unbaked = {}
    for description in descriptions:
        try:
            modifiers = xg.fxModules(str(palette), str(description)) or []
        except Exception:
            raise RuntimeError(u"XGen API 无法读取 Description {} 的 Modifier".format(description))

        for modifier in modifiers:
            try:
                if xg.fxModuleType(str(palette), str(description), str(modifier)) != "NoiseFXModule":
                    continue
                mode = xg.getAttr("mode", str(palette), str(description), str(modifier))
            except Exception:
                raise RuntimeError(
                    u'XGen API 无法读取 "{}"-"{}" 的 Noise 信息'.format(description, modifier)
                )

            if str(mode) == "0":
                unbaked.setdefault(description, []).append(modifier)
    return unbaked


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查 XGen Noise Modifier 是否已烘焙。"""
    try:
        palette = process_data.get("xgen_palette_name")
        descriptions = process_data.get("xgen_descriptions", [])

        if not palette:
            return u"没有获取到 XGen Palette 信息"
        if not descriptions:
            return u"没有获取到 XGen Description 信息"

        unbaked = _collect_unbaked(palette, descriptions)
        process_data["xgen_unbaked_noise"] = unbaked

        if not unbaked:
            return ""

        items = []
        for description, modifiers in unbaked.items():
            items.extend("{}-{}".format(description, modifier) for modifier in modifiers)

        return u"以下 Noise 修改器没有烘焙数据：{}".format(", ".join(items))
    except Exception:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """烘焙未完成的 XGen Noise Modifier。"""
    try:
        palette = process_data.get("xgen_palette_name")
        descriptions = process_data.get("xgen_descriptions", [])

        if not palette:
            return u"没有获取到 XGen Palette 信息"
        if not descriptions:
            return u"没有获取到 XGen Description 信息"

        unbaked = process_data.get("xgen_unbaked_noise")
        if unbaked is None:
            unbaked = _collect_unbaked(palette, descriptions)

        if not unbaked:
            return ""

        errors = []
        for description, modifiers in unbaked.items():
            try:
                if logger:
                    logger.info(u'开始烘焙 "{}"：{}'.format(description, ", ".join(modifiers)))

                for modifier in modifiers:
                    xg.setAttr("mode", "2", str(palette), str(description), str(modifier))

                mel.eval('xgmNullRender -pb "{}"'.format(description))

                for modifier in modifiers:
                    xg.setAttr("mode", "1", str(palette), str(description), str(modifier))

                if logger:
                    logger.info(u"Noise 烘焙完成：{}".format(description))
            except Exception:
                errors.append(description)
                for modifier in modifiers:
                    try:
                        xg.setAttr("mode", "0", str(palette), str(description), str(modifier))
                    except Exception:
                        pass

        process_data["xgen_unbaked_noise"] = {}

        if errors:
            return u"以下 Description 的 Noise 烘焙失败：{}".format(", ".join(errors))
        return ""
    except Exception:
        return traceback.format_exc()