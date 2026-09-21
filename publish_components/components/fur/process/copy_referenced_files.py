# -*- coding: utf-8 -*-
import os,glob,shutil,traceback
import maya.cmds as cmds
import maya.mel as mel
import maya.utils as utils
import xgenm as xg
from oct.pipeline import path_acs

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """拷贝资产依赖的 XGen 数据和贴图到版本目录，并重新设置引用路径。"""
    try:
        def save_scene(file_path):
            file_path=str(file_path).replace("\\","/").replace('"','\\"')
            mel.eval('file -rename "{}";'.format(file_path))
            mel.eval('file -save -force -type "mayaAscii";')

        def process():
            work_space_root=process_data.get("work_space_root")
            version_dir=process_data.get("version_dir")
            palette=process_data.get("xgen_palette_name")
            descriptions=process_data.get("xgen_descriptions",[])
            v_dir_ma_file=process_data.get("v_dir_ma_file")

            if not work_space_root:
                raise RuntimeError(u"没有获取到 work_space_root")
            if not version_dir:
                raise RuntimeError(u"没有获取到 version_dir")
            if not palette:
                raise RuntimeError(u"没有获取到 xgen_palette_name")
            if not descriptions:
                raise RuntimeError(u"没有获取到 xgen_descriptions")
            if not v_dir_ma_file:
                raise RuntimeError(u"没有获取到 v_dir_ma_file")

            work_space_root=str(work_space_root).replace("\\","/").rstrip("/")
            version_dir=str(version_dir).replace("\\","/").rstrip("/")
            v_dir_ma_file=str(v_dir_ma_file).replace("\\","/")

            core_palettes=set(str(item) for item in (xg.palettes() or []))
            if str(palette) not in core_palettes:
                raise RuntimeError(u"XGen Core 没有加载 Palette：{}".format(palette))

            src="{}/xgen/collections/{}".format(work_space_root,palette)
            target="{}/xgen/collections/{}".format(version_dir,palette)
            if not os.path.isdir(src):
                raise RuntimeError(u"XGen Collection 不存在：{}".format(src))
            if os.path.exists(target):
                shutil.rmtree(target)
            shutil.copytree(src,target)

            origin_paths=process_data.get("origin_paths") or {}
            origin_paths.setdefault("files",{})

            old_palette_path=xg.getAttr("xgDataPath",str(palette)) or ""
            origin_paths["xgDataPath"]=str(old_palette_path).replace("\\","/")

            description_paths={}
            new_xg_data_path=target.rstrip("/")+"/"

            xg.setAttr("xgDataPath",new_xg_data_path,str(palette))

            for description in descriptions:
                description=str(description).split("|")[-1]
                old_path=xg.getAttr("xgDataPath",str(palette),description) or ""
                description_paths[description]=str(old_path).replace("\\","/")
                xg.setAttr("xgDataPath",new_xg_data_path,str(palette),description)

            origin_paths["xgDescriptionDataPaths"]=description_paths

            file_dic={}
            for node in cmds.ls(type=["file","aiImage"]) or []:
                node_type=cmds.nodeType(node)
                image_path=cmds.getAttr(node+".computedFileTextureNamePattern") if node_type=="file" else cmds.getAttr(node+".filename")
                if not image_path:
                    continue
                image_path=str(image_path).replace("\\","/")
                if image_path.lower().startswith("i:/"):
                    continue
                file_dic[node]=image_path
                origin_paths["files"][node]=image_path

            process_data["origin_paths"]=origin_paths

            source_images=[]
            for image_path in file_dic.values():
                paths=glob.glob(image_path.replace("<UDIM>","*")) if "<UDIM>" in image_path else [image_path]
                for path in paths:
                    path=str(path).replace("\\","/")
                    if path not in source_images:
                        source_images.append(path)

            target_dir="{}/sourceimages_hair".format(version_dir)
            if not os.path.exists(target_dir):
                path_acs.make_dirs(target_dir)

            if logger:
                logger.info(u"开始拷贝毛发贴图，共 {} 个文件".format(len(source_images)))

            for image in source_images:
                if not os.path.isfile(image):
                    if logger:
                        logger.warning(u"毛发贴图不存在：{}".format(image))
                    continue
                target_image="{}/{}".format(target_dir,os.path.basename(image))
                if not os.path.exists(target_image):
                    shutil.copy2(image,target_image)

            for node,image_path in file_dic.items():
                target_path="{}/{}".format(target_dir,os.path.basename(image_path))
                if cmds.nodeType(node)=="file":
                    cmds.setAttr(node+".fileTextureName",target_path,type="string")
                else:
                    cmds.setAttr(node+".filename",target_path,type="string")

            save_scene(v_dir_ma_file)

            if logger:
                logger.info(u"XGen DataPath更新：{}".format(new_xg_data_path))
                logger.info(u"Fur依赖拷贝完成：{}".format(version_dir))

        utils.executeInMainThreadWithResult(process)
    except Exception:
        return traceback.format_exc()