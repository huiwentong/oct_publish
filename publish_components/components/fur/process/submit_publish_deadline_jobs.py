# -*- coding: utf-8 -*-
import os,traceback
from datetime import datetime
from oct.pipeline import deadline

POOL="production"
SECONDARY_POOL="user"
PRIORITY=70
DENY_LIST=["liulu","ls"]

def _submit_job(name,command,dependencies=None,logger=None):
    """提交 CommandLine Deadline Job。"""
    if logger:
        logger.info(u"提交 Deadline：{}".format(name))
        logger.info(command)
    job=deadline.CommandLineJob(name=name)
    job.set_command(command.replace("/",os.sep))
    job.set_job_error_limit(number=3)
    job.set_priority(priority=PRIORITY)
    job.set_deny_list(deny_list=DENY_LIST)
    job.set_pool(pool=POOL)
    job.set_secondary_pool(pool=SECONDARY_POOL)
    if dependencies:
        job.set_dependencies(parents=dependencies)
    job_id=job.submit()
    if not job_id:
        return None,u"提交 Deadline 任务失败：{}".format(name)
    return job_id,""

def _submit_xml(process_data,logger=None):
    """提交 XML 生成任务。"""
    ma_file=process_data.get("v_dir_ma_file")
    version_name=process_data.get("version_name")
    asset_type=process_data.get("sg_asset_type")
    if not ma_file:
        return None,u"没有获取到 v_dir_ma_file"
    if not version_name:
        return None,u"没有获取到 version_name"
    if not asset_type:
        return None,u"没有获取到 sg_asset_type"

    xml_mel="Z:/DS/Work/TD/liulu/Dev/thirdparty/m2k/xml_script.mel"
    command='rez-env toolsets maya-2024 -- mayabatch -file "{}" -script "{}" -noAutoloadPlugins'.format(ma_file,xml_mel)
    name="[fur_xml] {}.{}".format(str(asset_type).lower(),version_name)
    return _submit_job(name,command,logger=logger)

def _submit_klf(xml_job_id,process_data,logger=None):
    """提交 KLF 生成任务，依赖 XML。"""
    version_name=process_data.get("version_name")
    project_name=process_data.get("project_name")
    asset_type=process_data.get("sg_asset_type")
    if not xml_job_id:
        return None,u"没有获取到 XML Deadline Job ID"
    if not version_name:
        return None,u"没有获取到 version_name"
    if not project_name:
        return None,u"没有获取到 project_name"
    if not asset_type:
        return None,u"没有获取到 sg_asset_type"

    proj_name=str(project_name).lower()
    script_file="Z:/DS/Work/TD/liulu/Dev/thirdparty/m2k/create_katana_file.py"
    xml_folder="W:/projects/{}/misc/depts/tex/M2K/xml".format(proj_name)
    tag_dir="{}.{}".format(str(asset_type).lower(),version_name)
    command='rez-env toolsets katana-7.5v2 -- katanaBin --script "{}" "{}" "{}" "{}"'.format(script_file,xml_folder,tag_dir,proj_name)
    name="[fur_klf] {}.upKLF_{}".format(version_name.rsplit(".",2)[0],datetime.now().strftime("%Y%m%d"))
    return _submit_job(name,command,[xml_job_id],logger)

def _submit_turntable(klf_job_id,process_data,logger=None):
    """KLF 完成后执行 tt_to_deadline，创建真正的 Turntable 任务。"""
    project_name=process_data.get("project_name")
    asset_name=process_data.get("entity_name")
    dept=process_data.get("step_name")
    task=process_data.get("task_name")
    if not klf_job_id:
        return None,u"没有获取到 KLF Deadline Job ID"
    if not project_name:
        return None,u"没有获取到 project_name"
    if not asset_name:
        return None,u"没有获取到 entity_name"
    if not dept:
        return None,u"没有获取到 step_name"
    if not task:
        return None,u"没有获取到 task_name"

    proj_name=str(project_name).lower()
    dept=str(dept).lower()
    rez_config=r"\\192.168.15.15\pipeline\config\rezconfig.py"
    command='cmd /c "set REZ_CONFIG_FILE={}&& rez-env oct_turntable_to_deadline -- tt_to_deadline {} {} {} {}"'.format(
        rez_config,proj_name,asset_name,dept,task
    )
    name="[fur_turntable_submit] {}.{}.{}".format(asset_name,dept,task)
    return _submit_job(name,command,[klf_job_id],logger)

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """提交 Fur Publish 后续 XML、KLF 和可选 Turntable Deadline 任务。"""
    try:
        version_name=process_data.get("version_name")
        asset_type=process_data.get("sg_asset_type")
        if not version_name:
            return u"没有获取到 version_name"
        if not asset_type:
            return u"没有获取到 sg_asset_type"

        asset_type=str(asset_type).upper()
        if asset_type=="SCN":
            return ""

        xml_id=process_data.get("xml_deadline_job_id")
        if not xml_id:
            xml_id,error=_submit_xml(process_data,logger)
            if error:
                return error
            process_data["xml_deadline_job_id"]=xml_id

        klf_id=process_data.get("klf_deadline_job_id")
        if not klf_id:
            klf_id,error=_submit_klf(xml_id,process_data,logger)
            if error:
                return error
            process_data["klf_deadline_job_id"]=klf_id

        if asset_type in ["CHR","CH","PROP","PRP"] and process_data.get("output_turntable",True):
            turntable_id=process_data.get("turntable_submit_deadline_job_id")
            if not turntable_id:
                turntable_id,error=_submit_turntable(klf_id,process_data,logger)
                if error:
                    return error
                process_data["turntable_submit_deadline_job_id"]=turntable_id

        if logger:
            logger.info(u"Deadline提交完成 XML:{} KLF:{} Turntable:{}".format(
                xml_id,klf_id,process_data.get("turntable_submit_deadline_job_id","")
            ))
        return ""
    except Exception:
        return traceback.format_exc()