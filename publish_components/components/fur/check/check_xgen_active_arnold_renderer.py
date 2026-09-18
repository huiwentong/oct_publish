# -*- coding: utf-8 -*-

import traceback

import xgenm as xg
import xgenm.xgGlobal as xgg


def _refresh_xgen():
    """刷新 XGen Description Editor。"""
    editor = getattr(xgg, "DescriptionEditor", None)

    if not editor:
        return

    try:
        editor.refresh("Full")
    except Exception:
        pass


def _get_invalid_descriptions(palette, descriptions):
    """获取 Renderer 设置不正确的 Description。"""
    invalid = []

    for description in descriptions:
        active_renderer = xg.getActive(str(palette), str(description), "Renderer")

        renderer = xg.getAttr("renderer", str(palette), str(description), "RendermanRenderer")

        if (active_renderer != "RendermanRenderer" or renderer != "Arnold Renderer"):
            invalid.append(description)

    return invalid


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查 XGen Description 是否启用 Arnold Renderer。"""
    try:
        palette = process_data.get("xgen_palette_name")
        descriptions = process_data.get("xgen_descriptions", [])

        if not palette:
            return u"没有获取到 XGen Palette 信息"

        if not descriptions:
            return u"没有获取到 XGen Description 信息"

        try:
            invalid = _get_invalid_descriptions(palette, descriptions)
        except Exception:
            return u"XGen API 无法读取 Renderer 设置：\n{}".format(traceback.format_exc())

        if invalid:
            return u"以下 Description 未正确启用 Arnold Renderer：\n{}".format("\n".join(invalid))

        return ""

    except Exception:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """自动将 XGen Description Renderer 设置为 Arnold Renderer。"""
    try:
        palette = process_data.get("xgen_palette_name")
        descriptions = process_data.get("xgen_descriptions", [])

        if not palette:
            return u"没有获取到 XGen Palette 信息"

        if not descriptions:
            return u"没有获取到 XGen Description 信息"

        try:
            invalid = _get_invalid_descriptions(palette, descriptions)
        except Exception:
            return u"XGen API 无法读取 Renderer 设置：\n{}".format(traceback.format_exc())

        if not invalid:
            return ""

        errors = []

        for description in invalid:
            try:
                if logger:
                    logger.warning(u'AUTO FIX: 设置 Description "{}" 使用 Arnold Renderer'.format(description))

                xg.setActive(str(palette), str(description), "RendermanRenderer")

                xg.setAttr("renderer", "Arnold Renderer", str(palette), str(description), "RendermanRenderer")

            except Exception:
                errors.append(description)

        _refresh_xgen()

        if errors:
            return u"以下 Description 的 Arnold Renderer 修复失败：{}".format(", ".join(errors))

        try:
            invalid = _get_invalid_descriptions(palette, descriptions)
        except Exception:
            return u"修复后无法重新检查 Renderer：\n{}".format(traceback.format_exc())

        if invalid:
            return u"以下 Description 修复后仍未正确启用 Arnold Renderer：\n{}".format("\n".join(invalid))
        return ""

    except Exception:
        return traceback.format_exc()