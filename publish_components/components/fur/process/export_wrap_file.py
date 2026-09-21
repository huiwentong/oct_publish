# -*- coding: utf-8 -*-
import re,traceback
import maya.cmds as cmds
import maya.mel as mel
import maya.utils as utils

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """导出 Hair_xgenBaseGeo 包裹文件，并清理 Arnold 属性。"""
    try:
        def process():
            version_dir=process_data.get("version_dir")
            entity_name=process_data.get("entity_name")

            if not version_dir:
                raise RuntimeError(u"没有获取到 version_dir")
            if not entity_name:
                raise RuntimeError(u"没有获取到 entity_name")
            if not cmds.objExists("Hair_xgenBaseGeo"):
                raise RuntimeError(u"场景中不存在 Hair_xgenBaseGeo")

            version_dir=str(version_dir).replace("\\","/").rstrip("/")
            wrap_file="{}/{}.wrap.ma".format(version_dir,entity_name)

            mel.eval("select -cl;")
            mel.eval('select -r "Hair_xgenBaseGeo";')
            mel.eval('file -force -options "v=0;" -typ "mayaAscii" -pr -es "{}";'.format(wrap_file.replace('"','\\"')))

            with open(wrap_file,"r",encoding="utf-8",errors="replace") as f:
                ma_data=f.read()

            ma_data=re.sub(r'  setAttr ".ai_translator" -type "string" (.*?);',"",ma_data)

            with open(wrap_file,"w",encoding="utf-8") as f:
                f.write(ma_data)

            process_data["wrap_file"]=wrap_file

            if logger:
                logger.info(u"Wrap 文件导出完成：{}".format(wrap_file))

        utils.executeInMainThreadWithResult(process)
    except Exception:
        return traceback.format_exc()