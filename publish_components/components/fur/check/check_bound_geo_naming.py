# -*- coding: utf-8 -*-
import re,traceback

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """检查 XGen 生长面命名是否符合 对应名称_Hair_Face 规范。"""
    try:
        bound_geometry=process_data.get("xgen_bound_geometry",[])
        if not bound_geometry:
            return u"没有获取到 XGen 生长面信息"

        error_list=[]
        for bound_geo in bound_geometry:
            short_name=bound_geo.split("|")[-1].split(":")[-1]
            if not re.match(r"^.+_Hair_Face$",short_name):
                error_list.append(short_name)

        if error_list:
            return u"生长面命名不规范：{}，应该为 对应名称_Hair_Face".format(", ".join(error_list))

        if logger:
            logger.info(u"XGen 生长面命名检查通过")
    except Exception:
        return traceback.format_exc()