# -*- coding: utf-8 -*-

import traceback

# All system check classes will use StdCheck as the class name.
class StdCheck():

    def __init__(self, dialog):
        self.dialog = dialog
        self.check_name  = u'检查贴图路径属性是否锁定'
        self.description = u"检查当前文件中贴图路径属性是否被锁定"
        self.auto_fix    = True
        self.duty        = u'艺术家本人。'
        return


    def run_check(self):
        import pymel.core as pm
        self.__locked_attr = list()

        try:
            for node in pm.ls(typ='file'): 
                if node.fileTextureName.isLocked():
                    self.__locked_attr.append(node.fileTextureName)

            for node in pm.ls(typ='aiImage'): 
                if node.filename.isLocked():
                    self.__locked_attr.append(node.filename)

            if self.__locked_attr:
                return u'发现以下贴图路径属性被锁定:\n{0}'.format('\n'.join([attr.name() for attr in self.__locked_attr]))
            else:
                return str()

        except:
            return traceback.format_exc()



    def run_fix(self):
        '''
        Auto Fix
        '''
        for attr in self.__locked_attr:
            attr.unlock()

        return str()



    def get_check_name(self):
        '''
        '''
        return self.check_name



    def get_description(self):
        '''
        '''
        return self.description



    def get_auto_fix(self):
        '''
        '''
        return self.auto_fix



    def get_duty(self):
        '''
        '''
        return self.duty

