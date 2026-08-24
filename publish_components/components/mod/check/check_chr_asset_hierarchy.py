# -*- coding: utf-8 -*-
import traceback
import maya.cmds as cmds
import maya.utils as utils
from textwrap import dedent
from importlib import reload
from oct.pipeline.task_context import TaskContext
from publish_components.utils.maya_utils import dialogs
reload(dialogs)
def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
    检查类人角色资产，high|body组下的节点名称和层级顺序
    """
    try:
        task_id = process_data['task_id']
        tc = TaskContext(task_id) or TaskContext.from_env()
        if tc.entity.sg_asset_type == "CH":
            valid_nodes = ['|Root_grp|Geo_grp|high|body|body_Geo',
                           '|Root_grp|Geo_grp|high|body|teeth_Geo',
                           '|Root_grp|Geo_grp|high|body|eye_L|eyeball_L_Geo',
                           '|Root_grp|Geo_grp|high|body|eye_L|eyeshell_L_Geo',
                           '|Root_grp|Geo_grp|high|body|eye_L|eyeedge_L_Geo',
                           '|Root_grp|Geo_grp|high|body|eye_L|leixian_L_Geo',
                           '|Root_grp|Geo_grp|high|body|eye_L',
                           '|Root_grp|Geo_grp|high|body|eye_R|eyeball_R_Geo',
                           '|Root_grp|Geo_grp|high|body|eye_R|eyeshell_R_Geo',
                           '|Root_grp|Geo_grp|high|body|eye_R|eyeedge_R_Geo',
                           '|Root_grp|Geo_grp|high|body|eye_R|leixian_R_Geo',
                           '|Root_grp|Geo_grp|high|body|eye_R']

            body_p = "|Root_grp|Geo_grp|high|body"
            child_fp = cmds.listRelatives(body_p, allDescendents=True, fullPath=1, type="transform")
            message = ''
            if not child_fp == valid_nodes:
                message = dedent("""
                                  类人形资产 high|body 下的组和模型要严格按照下面的格式严格保持 '名字', '顺序', '数量'：
                                    body
                                    ----body_Geo
                                    ----teeth_Geo
                                    ----eye_L
                                        ----eyeball_L_Geo
                                        ----eyeshell_L_Geo
                                        ----eyeedge_L_Geo
                                        ----leixian_L_Geo
                                    ----eye_R
                                        ----eyeball_R_Geo
                                        ----eyeshell_R_Geo
                                        ----eyeedge_R_Geo
                                        ----leixian_R_Geo
                                  非类人资产可以跳过该检查项！
                                  """)
                if parent_widget:
                    result =  utils.executeInMainThreadWithResult(lambda:dialogs.message_dialog("提示", message, ["跳过检查", "停止提交"]))
                    if result == "停止提交":
                        return message
    except:
        return traceback.format_exc()


