# -*- coding: utf-8 -*-
import os,re,tempfile,traceback
from pxr import Usd
from glob import glob
from oct.pipeline.path_acs import make_dirs
from oct.data.usd import step_pub_usds
from publish_components.utils.maya_utils.export_usd_core import batch_export_fur_usd

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """导出 Fur Arnold high.usd，并生成正式 Fur USD。"""

    def delete_xgen_from_ma(ma_file):
        new_ma = ""
        with open(ma_file, 'r') as f:
            all = f.read()
            new_ma = re.sub("requires -dataType \"xgm[\W\w]*?requires", "requires", all)

        tmp_dir = tempfile.gettempdir()
        new_ma_file = os.path.join(tmp_dir, os.path.basename(ma_file)).replace('\\', '/')
        new_ma_file = os.path.expanduser(new_ma_file)
        with open(new_ma_file, 'w') as f:
            f.write(new_ma)
        print(new_ma_file)
        return new_ma_file

    temp_shader_ma = ""
    try:
        usd_dir = process_data["v_dir_usd"]
        task_id = process_data.get("task_id")
        mat_map = process_data.get("mat_map")
        version_dir = process_data.get("version_dir")
        version_dir = str(version_dir).replace("\\","/").rstrip("/")
        high_usd = "{}/high.usd".format(usd_dir)
        xgen_file = glob(version_dir + '/*.xgen')[0]
        xgen_file = str(xgen_file).replace("\\","/")
        shader_ma = "{}/srf_shaders.ma".format(version_dir)
        geom_file = "{}/alembic/base.abc".format(version_dir)

        if not os.path.isfile(shader_ma):
            raise RuntimeError(u"没有找到材质文件：{}".format(shader_ma))
        if not os.path.isfile(xgen_file):
            raise RuntimeError(u"没有找到 XGen 文件：{}".format(xgen_file))
        if not os.path.isfile(geom_file):
            raise RuntimeError(u"没有找到绑定模型：{}".format(geom_file))

        if not os.path.exists(usd_dir):
            make_dirs(usd_dir)

        temp_shader_ma = delete_xgen_from_ma(shader_ma)
        batch_export_fur_usd(temp_shader_ma, high_usd)
        Usd.Stage.Open(high_usd)
        step_pub_usds.FurStepUsd(version_folder=version_dir, task_id=task_id,
                                 xgen_file=xgen_file, geom_file=geom_file, mat_map=mat_map)

    except Exception:
        return traceback.format_exc()

    finally:
        if temp_shader_ma and os.path.isfile(temp_shader_ma):
            try:
                os.remove(temp_shader_ma)
            except Exception:
                pass