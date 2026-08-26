# -*- coding: utf-8 -*-

import os
import traceback

# All system check classes will use StdCheck as the class name.
class StdCheck():

    def __init__(self, dialog):
        self.dialog = dialog
        self.check_name = u"检查root_jnt下的所有骨骼的属性不可锁定"
        self.description = u"检查root_jnt下的所有骨骼的属性不可锁定"
        self.auto_fix = True
        self.duty = u"艺术家本人。"
        return


    def run_check(self):
        import maya.cmds as cmds
        try:     
            if cmds.objExists('root_jnt'):
                bad_jnts = []
                jnts = cmds.listRelatives('root_jnt', ad=1, type='joint', f=1)
                if jnts:
                    for jnt in jnts:
                        for attr in ['tx','ty','tz','rx','ry','rz','sx','sy','sz']:
                            if cmds.getAttr(jnt+'.'+attr, l=1):
                                if jnt not in bad_jnts:
                                    bad_jnts.append(jnt)
                if bad_jnts:
                    return u"root骨骼下有骨骼属性被锁定:{}".format(bad_jnts)

            return ""

        except:
            return traceback.format_exc()

    def run_fix(self):
        '''Auto Fix'''
        if cmds.objExists('root_jnt'):
            jnts = cmds.listRelatives('root_jnt', ad=1, type='joint', f=1)
            for jnt in jnts:
                for attr in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz']:
                    cmds.setAttr(jnt+'.'+attr, k=1, l=0)

        return self.auto_fix

    def get_check_name(self):
        return self.check_name

    def get_description(self):
        return self.description

    def get_auto_fix(self):
        return self.auto_fix

    def get_duty(self):
        return self.duty

