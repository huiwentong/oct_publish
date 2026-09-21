# -*- coding: utf-8 -*-
import traceback
import maya.mel as mel

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """检查场景中是否存在 Unknown Plugin。"""
    try:
        def get_unknown_plugins():
            plugins=mel.eval('unknownPlugin -q -l;') or []
            if isinstance(plugins,str):
                plugins=[plugins]
            return plugins

        unknown_plugins=get_unknown_plugins()
        if unknown_plugins:
            raise RuntimeError(u"场景中存在 Unknown Plugin：{}".format(", ".join(unknown_plugins)))

        if logger:
            logger.info(u"Unknown Plugin 检查通过")
    except Exception:
        return traceback.format_exc()

def fix(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """清理场景中的 Unknown Plugin。"""
    try:
        def get_unknown_plugins():
            plugins=mel.eval('unknownPlugin -q -l;') or []
            if isinstance(plugins,str):
                plugins=[plugins]
            return plugins

        unknown_plugins=get_unknown_plugins()
        errors=[]

        for plugin in unknown_plugins:
            try:
                plugin_name=plugin.replace("\\","\\\\").replace('"','\\"')
                mel.eval('unknownPlugin -remove "{}";'.format(plugin_name))
                if logger:
                    logger.info(u"删除 Unknown Plugin：{}".format(plugin))
            except Exception:
                errors.append(plugin)
                if logger:
                    logger.warning(u"无法删除 Unknown Plugin：{}".format(plugin))

        if errors:
            raise RuntimeError(u"以下 Unknown Plugin 无法删除：{}".format(", ".join(errors)))

        if logger:
            logger.info(u"Unknown Plugin 清理完成")
    except Exception:
        return traceback.format_exc()