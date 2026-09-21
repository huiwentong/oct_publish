# -*- coding: utf-8 -*-
import traceback
import maya.cmds as cmds
import maya.mel as mel
import maya.utils as utils

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """导出 XGen 材质 ma 文件和材质分配信息。"""
    try:
        def process():
            version_dir=process_data.get("version_dir")
            if not version_dir:
                raise RuntimeError(u"没有获取到 version_dir")

            sgs=mel.eval('ls -type "shadingEngine";') or []
            if isinstance(sgs,str):
                sgs=[sgs]

            list_sgs=[]
            for sg in sgs:
                if sg in ["initialParticleSE","initialShadingGroup"]:
                    continue

                descriptions=cmds.listConnections(sg,s=True,d=False,sh=True,type="xgmDescription") or []
                if not descriptions:
                    continue

                attr=sg+".assignedXgmDescriptions"
                if not cmds.objExists(attr):
                    cmds.addAttr(sg,ln="assignedXgmDescriptions",dt="string")

                cmds.setAttr(attr,";".join(descriptions),type="string")
                list_sgs.append(sg)

            if not list_sgs:
                raise RuntimeError(u"XGen没有赋给材质")

            mel.eval("select -cl;")
            nodes=" ".join('"{}"'.format(node.replace('"','\\"')) for node in list_sgs)
            mel.eval("select -r -ne {};".format(nodes))

            version_dir=str(version_dir).replace("\\","/").rstrip("/")
            output_file="{}/srf_shaders.ma".format(version_dir)
            mel.eval('file -force -options "v=0;" -typ "mayaAscii" -pr -es "{}";'.format(output_file.replace('"','\\"')))
            process_data["xgen_shader_file"]=output_file

            if logger:
                logger.info(u"材质导出完成：{}".format(output_file))

        utils.executeInMainThreadWithResult(process)
    except Exception:
        return traceback.format_exc()