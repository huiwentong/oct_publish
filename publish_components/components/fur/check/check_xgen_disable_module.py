# -*- coding: utf-8 -*-

import traceback
import xgenm as xg


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查 XGen Modifier 是否处于禁用状态。"""
    try:
        palette = process_data.get("xgen_palette_name")
        descriptions = process_data.get("xgen_descriptions", [])

        if not palette:
            return u"没有获取到 XGen Palette 信息"

        if not descriptions:
            return u"没有获取到 XGen Description 信息"

        errors = []

        for description_path in descriptions:
            description = description_path.split("|")[-1]

            try:
                modifiers = xg.fxModules(str(palette), str(description)) or []
            except Exception:
                return u"XGen API 无法读取 Description {} 的 Modifier".format(description)

            for modifier in modifiers:
                try:
                    active = xg.getAttr("active", str(palette), str(description), str(modifier))
                except Exception:
                    return u'XGen API 无法读取 "{}"-"{}" 的 active 属性'.format(description, modifier)

                if str(active).strip().lower() in ("false", "0"):
                    errors.append(u'"{}"-"{}" 修改器未启用，如不需要请删除'.format(description, modifier))

        if errors:
            return "\n".join(errors)

        return ""

    except Exception:
        return traceback.format_exc()