# -*- coding: utf-8 -*-
import os,glob,shutil,traceback
import pymel.core as pm
import maya.utils as utils
import xgenm as xg
from oct.pipeline import path_acs

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """拷贝资产依赖的 XGen 数据和贴图到版本目录，并重新设置引用路径。"""
    try:
        def process():
            work_space_root = process_data.get("work_space_root")
            version_dir = process_data.get("version_dir")
            v_dir_ma_file = process_data.get("v_dir_ma_file")
            work_space_root = str(work_space_root).replace("\\","/").rstrip("/")
            version_dir = str(version_dir).replace("\\","/").rstrip("/")
            v_dir_ma_file = str(v_dir_ma_file).replace("\\","/")

            palettes = xg.palettes()
            if len(palettes) != 1:
                return u"xgen palette数量不是一个， 请检查"
            palette = palettes[0]
            descriptions = xg.descriptions(palette)

            src = "{}/xgen/collections/{}".format(work_space_root,palette)
            target = "{}/xgen/collections/{}".format(version_dir,palette)
            if not os.path.isdir(src):
                raise RuntimeError(u"XGen Collection 不存在：{}".format(src))
            if os.path.exists(target):
                shutil.rmtree(target)
            shutil.copytree(src,target)

            origin_paths = process_data.get("origin_paths") or {}
            origin_paths.setdefault("files", {})
            old_palette_path = xg.getAttr("xgDataPath", str(palette)) or ""
            origin_paths["xgDataPath"] = str(old_palette_path).replace("\\","/")

            description_paths = {}
            new_xg_data_path = target.rstrip("/") + "/"
            new_proj_path = version_dir.rstrip("/") + "/"
            xg.setAttr("xgDataPath", new_xg_data_path, str(palette))
            xg.setAttr("xgProjectPath", new_proj_path, str(palette))

            for description in descriptions:
                description = str(description).split("|")[-1]
                old_path = xg.getAttr("xgDataPath", str(palette), description) or ""
                description_paths[description] = str(old_path).replace("\\","/")
                xg.setAttr("xgDataPath", new_xg_data_path, str(palette), description)

            origin_paths["xgDescriptionDataPaths"]=description_paths
            file_dic={}
            for node in pm.ls(type=["file","aiImage"]) or []:
                node_type = pm.nodeType(node)
                image_path = pm.getAttr(node+".computedFileTextureNamePattern") if node_type=="file" else pm.getAttr(node+".filename")
                if not image_path:
                    continue
                image_path = str(image_path).replace("\\","/")
                if image_path.lower().startswith("i:/"):
                    continue
                file_dic[node] = image_path
                origin_paths["files"][node] = image_path

            process_data["origin_paths"] = origin_paths

            source_images = []
            for image_path in file_dic.values():
                paths = glob.glob(image_path.replace("<UDIM>","*")) if "<UDIM>" in image_path else [image_path]
                for path in paths:
                    path = str(path).replace("\\","/")
                    if path not in source_images:
                        source_images.append(path)

            target_dir = "{}/sourceimages_hair".format(version_dir)
            if not os.path.exists(target_dir):
                path_acs.make_dirs(target_dir)

            logger.info(u"开始拷贝毛发贴图，共 {} 个文件".format(len(source_images)))

            for image in source_images:
                if not os.path.isfile(image):
                    logger.warning(u"毛发贴图不存在：{}".format(image))
                    continue

                target_image = "{}/{}".format(target_dir,os.path.basename(image))
                if not os.path.exists(target_image):
                    shutil.copy2(image,target_image)

            for node,image_path in file_dic.items():
                target_path = "{}/{}".format(target_dir,os.path.basename(image_path))
                if pm.nodeType(node) == "file":
                    pm.setAttr(node+".fileTextureName",target_path, type="string")
                else:
                    pm.setAttr(node+".filename",target_path, type="string")

            pm.saveAs(v_dir_ma_file, force=True)
            logger.info(u"XGen DataPath更新：{}".format(new_xg_data_path))
            logger.info(u"XGen ProjectPath更新：{}".format(new_proj_path))
            logger.info(u"Fur依赖拷贝完成：{}".format(version_dir))

            return None

        utils.executeInMainThreadWithResult(process)
    except Exception:
        return traceback.format_exc()