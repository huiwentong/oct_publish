# -*- coding: utf-8 -*-
import os,re,shutil,tempfile,subprocess,traceback
from pxr import Usd
from oct.data.usd import step_pub_usds

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """导出 Fur Arnold high.usd，并生成正式 Fur USD。"""
    temp_shader_ma=None
    try:
        SUCCESS_MARKER="__OCT_USD_EXPORT_SUCCESS__"

        def delete_xgen_from_ma(ma_file):
            """移除材质 Maya 文件中的 XGen requires，生成临时 MA。"""
            with open(ma_file,"r",encoding="utf-8",errors="replace") as f:
                context=f.read()
            context=re.sub(r'requires -dataType "xgm[\W\w]*?requires',"requires",context)
            temp_ma=os.path.join(tempfile.gettempdir(),os.path.basename(ma_file)).replace("\\","/")
            with open(temp_ma,"w",encoding="utf-8") as f:
                f.write(context)
            return temp_ma

        def get_utils_env():
            """继承当前 Publisher 环境给 rez/mayapy 子进程。"""
            env=os.environ.copy()
            env["PYTHONIOENCODING"]="utf-8"
            return env

        def build_export_script(shader_ma,shader_usd):
            """生成独立 mayapy Arnold USD 导出脚本。"""
            return r'''# -*- coding: utf-8 -*-
import os,sys,traceback
import maya.standalone
maya.standalone.initialize(name="python")
import maya.cmds as cmds

SHADER_MA=r"{shader_ma}"
SHADER_USD=r"{shader_usd}"
SUCCESS_MARKER="{success_marker}"

def create_cubes_for_all_materials():
    materials=cmds.ls(materials=True) or []
    print("[USD] material count:",len(materials))
    for i,mat in enumerate(materials):
        try:
            cube=cmds.polyCube(name="{{}}_cube".format(mat))[0]
            cmds.move(i*3,0,0,cube)
            sg_nodes=cmds.listConnections(mat,type="shadingEngine") or []
            if not sg_nodes:
                sg=cmds.sets(renderable=True,noSurfaceShader=True,empty=True,name="{{}}SG".format(mat))
                if cmds.objExists(mat+".outColor"):
                    cmds.connectAttr(mat+".outColor",sg+".surfaceShader",force=True)
                sg_nodes=[sg]
            cmds.sets(cube,edit=True,forceElement=sg_nodes[0])
        except Exception:
            traceback.print_exc()

cmds.loadPlugin("mtoa",quiet=True)
try:
    cmds.loadPlugin("mayaUsdPlugin",quiet=True)
except Exception:
    traceback.print_exc()

cmds.file(SHADER_MA,open=True,force=True,ignoreVersion=True)

if cmds.objExists("defaultRenderGlobals.outFormatControl"):
    cmds.setAttr("defaultRenderGlobals.outFormatControl",0)

create_cubes_for_all_materials()
cmds.select(all=True)

if os.path.isfile(SHADER_USD):
    os.remove(SHADER_USD)

print("[USD] Exporting Arnold Scene...")
sys.stdout.flush()

cmds.arnoldExportAss(
    f=SHADER_USD,
    mask=14584,
    lightLinks=0,
    shadowLinks=0,
    fullPath=1,
    exportAllShadingGroups=1,
    writeDefaults=True
)

if not os.path.isfile(SHADER_USD):
    raise RuntimeError("high.usd was not created: {{}}".format(SHADER_USD))
if os.path.getsize(SHADER_USD)<=0:
    raise RuntimeError("high.usd is empty: {{}}".format(SHADER_USD))

print(SUCCESS_MARKER)
sys.stdout.flush()
sys.stderr.flush()
os._exit(0)
'''.format(
                shader_ma=shader_ma.replace("\\","/"),
                shader_usd=shader_usd.replace("\\","/"),
                success_marker=SUCCESS_MARKER
            )

        def export_high_usd(shader_ma,high_usd):
            """通过独立 mayapy 导出 Arnold high.usd。"""
            script_path=None
            try:
                code=build_export_script(shader_ma,high_usd)
                with tempfile.NamedTemporaryFile(mode="w",delete=False,suffix=".py",encoding="utf-8") as f:
                    f.write(code)
                    script_path=f.name

                cmd='rez-env maya-2024 mtoa -c "mayapy.exe {}"'.format(script_path)
                if logger:
                    logger.info(u"Arnold USD export command: {}".format(cmd))

                process=subprocess.Popen(
                    cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    env=get_utils_env()
                )
                stdout,_=process.communicate()
                if isinstance(stdout,bytes):
                    stdout=stdout.decode("utf-8",errors="replace")
                if stdout:
                    print(stdout)

                if SUCCESS_MARKER not in stdout:
                    raise RuntimeError(
                        u"Arnold USD 子进程没有返回成功标记。\nreturncode={}\n{}".format(
                            process.returncode,stdout
                        )
                    )
                if not os.path.isfile(high_usd):
                    raise RuntimeError(u"没有生成 high.usd：{}".format(high_usd))
                if os.path.getsize(high_usd)<=0:
                    raise RuntimeError(u"high.usd 文件为空：{}".format(high_usd))
                if not Usd.Stage.Open(high_usd):
                    raise RuntimeError(u"high.usd 无法被 USD 正常打开：{}".format(high_usd))

                if logger:
                    logger.info(u"high.usd 验证成功：{}".format(high_usd))
            finally:
                if script_path and os.path.isfile(script_path):
                    try:
                        os.remove(script_path)
                    except Exception:
                        pass

        version_dir=process_data.get("version_dir")
        entity_name=process_data.get("entity_name")
        task_id=process_data.get("task_id")
        palette_name=process_data.get("xgen_palette_name")
        xgen_file=process_data.get("xgen_file")
        mat_map=process_data.get("mat_map")

        if not version_dir:
            raise RuntimeError(u"没有获取到 version_dir")
        if not entity_name:
            raise RuntimeError(u"没有获取到 entity_name")
        if not task_id:
            raise RuntimeError(u"没有获取到 task_id")
        if not palette_name:
            raise RuntimeError(u"没有获取到 xgen_palette_name")
        if not xgen_file:
            raise RuntimeError(u"没有获取到 xgen_file，请确认 export_xgen_file 已成功执行")
        if not mat_map:
            raise RuntimeError(u"没有获取到 mat_map，请确认 build_fur_mat_map 已成功执行")

        version_dir=str(version_dir).replace("\\","/").rstrip("/")
        xgen_file=str(xgen_file).replace("\\","/")
        shader_ma="{}/srf_shaders.ma".format(version_dir)
        geom_file="{}/alembic/base.abc".format(version_dir)
        usd_dir="{}/usd".format(version_dir)
        high_usd="{}/high.usd".format(usd_dir)

        if not os.path.isfile(shader_ma):
            raise RuntimeError(u"没有找到材质文件：{}".format(shader_ma))
        if not os.path.isfile(xgen_file):
            raise RuntimeError(u"没有找到 XGen 文件：{}".format(xgen_file))
        if not os.path.isfile(geom_file):
            raise RuntimeError(u"没有找到绑定模型：{}".format(geom_file))

        if os.path.isdir(usd_dir):
            shutil.rmtree(usd_dir)
        os.makedirs(usd_dir)

        if logger:
            logger.info(u"开始准备 Arnold 材质场景：{}".format(shader_ma))

        temp_shader_ma=delete_xgen_from_ma(shader_ma)
        export_high_usd(temp_shader_ma,high_usd)

        process_data["high_usd"]=high_usd

        if logger:
            logger.info(u"开始生成 Fur 正式 USD")

        step_pub_usds.FurStepUsd(
            version_folder=version_dir,
            task_id=task_id,
            xgen_file=xgen_file,
            geom_file=geom_file,
            mat_map=mat_map
        )

        if logger:
            logger.info(u"Fur USD 导出完成")
    except Exception:
        return traceback.format_exc()
    finally:
        if temp_shader_ma and os.path.isfile(temp_shader_ma):
            try:
                os.remove(temp_shader_ma)
            except Exception:
                pass