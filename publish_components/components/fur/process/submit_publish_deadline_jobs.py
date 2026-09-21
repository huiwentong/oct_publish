# -*- coding: utf-8 -*-
import os,traceback
from datetime import datetime
from oct.pipeline import deadline

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """提交 Fur Publish 后续 XML、KLF 和可选 Turntable Deadline 任务。"""
    try:
        POOL="production"
        SECONDARY_POOL="user"
        PRIORITY=70
        DENY_LIST=["liulu","ls"]

        def submit_job(name,command,dependencies=None):
            """提交 CommandLine Deadline Job。"""
            if logger:
                logger.info(u"提交 Deadline：{}".format(name))
                logger.info(command)

            job=deadline.CommandLineJob(name=name)
            job.set_command(command)
            job.set_job_error_limit(number=3)
            job.set_priority(priority=PRIORITY)
            job.set_deny_list(deny_list=DENY_LIST)
            job.set_pool(pool=POOL)
            job.set_secondary_pool(pool=SECONDARY_POOL)

            if dependencies:
                job.set_dependencies(parents=dependencies)

            job_id=job.submit()
            if not job_id:
                raise RuntimeError(u"提交 Deadline 任务失败：{}".format(name))
            return job_id

        def submit_xml():
            """提交 XML 生成任务。"""
            ma_file=process_data.get("v_dir_ma_file")
            version_name=process_data.get("version_name")
            asset_type=process_data.get("sg_asset_type")

            if not ma_file:
                raise RuntimeError(u"没有获取到 v_dir_ma_file")
            if not version_name:
                raise RuntimeError(u"没有获取到 version_name")
            if not asset_type:
                raise RuntimeError(u"没有获取到 sg_asset_type")

            ma_file=str(ma_file).replace("\\","/")
            xml_mel="Z:/DS/Work/TD/liulu/Dev/thirdparty/m2k/xml_script.mel"
            command='rez-env toolsets maya-2024 -- mayabatch -file "{}" -script "{}" -noAutoloadPlugins'.format(ma_file,xml_mel)
            name="[fur_xml] {}.{}".format(str(asset_type).lower(),version_name)
            return submit_job(name,command)

        def submit_klf(xml_job_id):
            """提交 KLF 生成任务，依赖 XML。"""
            version_name=process_data.get("version_name")
            project_name=process_data.get("project_name")
            asset_type=process_data.get("sg_asset_type")

            if not xml_job_id:
                raise RuntimeError(u"没有获取到 XML Deadline Job ID")
            if not version_name:
                raise RuntimeError(u"没有获取到 version_name")
            if not project_name:
                raise RuntimeError(u"没有获取到 project_name")
            if not asset_type:
                raise RuntimeError(u"没有获取到 sg_asset_type")

            proj_name=str(project_name).lower()
            script_file="Z:/DS/Work/TD/liulu/Dev/thirdparty/m2k/create_katana_file.py"
            xml_folder="W:/projects/{}/misc/depts/tex/M2K/xml".format(proj_name)
            tag_dir="{}.{}".format(str(asset_type).lower(),version_name)
            command='rez-env toolsets katana-7.5v2 -- katanaBin --script "{}" "{}" "{}" "{}"'.format(
                script_file,xml_folder,tag_dir,proj_name
            )
            name="[fur_klf] {}.upKLF_{}".format(version_name.rsplit(".",2)[0],datetime.now().strftime("%Y%m%d"))
            return submit_job(name,command,[xml_job_id])

        def submit_turntable(klf_job_id):
            """KLF 完成后执行 tt_to_deadline，创建真正的 Turntable 任务。"""
            project_name=process_data.get("project_name")
            asset_name=process_data.get("entity_name")
            dept=process_data.get("step_name")
            task=process_data.get("task_name")

            if not klf_job_id:
                raise RuntimeError(u"没有获取到 KLF Deadline Job ID")
            if not project_name:
                raise RuntimeError(u"没有获取到 project_name")
            if not asset_name:
                raise RuntimeError(u"没有获取到 entity_name")
            if not dept:
                raise RuntimeError(u"没有获取到 step_name")
            if not task:
                raise RuntimeError(u"没有获取到 task_name")

            proj_name=str(project_name).lower()
            dept=str(dept).lower()
            rez_config=r"\\192.168.15.15\pipeline\config\rezconfig.py"
            command='cmd.exe /c "set REZ_CONFIG_FILE={}&& rez-env oct_turntable_to_deadline -- tt_to_deadline {} {} {} {}"'.format(
                rez_config,proj_name,asset_name,dept,task
            )
            name="[fur_turntable_submit] {}.{}.{}".format(asset_name,dept,task)
            return submit_job(name,command,[klf_job_id])

        version_name=process_data.get("version_name")
        asset_type=process_data.get("sg_asset_type")

        if not version_name:
            raise RuntimeError(u"没有获取到 version_name")
        if not asset_type:
            raise RuntimeError(u"没有获取到 sg_asset_type")

        asset_type=str(asset_type).upper()

        if asset_type!="SCN":
            xml_id=process_data.get("xml_deadline_job_id")
            if not xml_id:
                xml_id=submit_xml()
                process_data["xml_deadline_job_id"]=xml_id

            klf_id=process_data.get("klf_deadline_job_id")
            if not klf_id:
                klf_id=submit_klf(xml_id)
                process_data["klf_deadline_job_id"]=klf_id

            if asset_type in ["CHR","CH","PROP","PRP"] and process_data.get("output_turntable",True):
                turntable_id=process_data.get("turntable_submit_deadline_job_id")
                if not turntable_id:
                    turntable_id=submit_turntable(klf_id)
                    process_data["turntable_submit_deadline_job_id"]=turntable_id

            if logger:
                logger.info(u"Deadline提交完成 XML:{} KLF:{} Turntable:{}".format(
                    xml_id,klf_id,process_data.get("turntable_submit_deadline_job_id","")
                ))
    except Exception:
        return traceback.format_exc()