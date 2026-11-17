# -*- coding: utf-8 -*-
import traceback, os
import importlib
from oct.pipeline import path_acs

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """导出模板相机和调色板 abc"""
    try:
        pm = importlib.import_module("pymel.core")
        utils = importlib.import_module("maya.utils")
        def process():
            template_nodes_map = {
                '|turntable_3points|rotate|cameras|wholeCam|Whole'             :    'camWhole.abc',
                '|turntable_3points|rotate|cameras|wholeCam|color_p_whole'     :    'colorpanelsWhole.abc',
                '|turntable_3points|rotate|cameras|uperCam|Uper'               :    'camUpper.abc',
                '|turntable_3points|rotate|cameras|uperCam|color_p_uper'       :    'colorpanelsUpper.abc',
                '|turntable_3points|rotate|cameras|closeupCam|Closeup'         :    'camCloseup.abc',
                '|turntable_3points|rotate|cameras|closeupCam|color_p_closeup' :    'colorpanelsCloseup.abc',
            }
            pm.loadPlugin('AbcExport', quiet=True)
            v_dir_abc = process_data['v_dir_abc']
            if not os.path.exists(v_dir_abc):
                path_acs.make_dirs(v_dir_abc)

            for node_full, abc_name in template_nodes_map.items():
                if not pm.objExists(node_full):
                    logger.warning("模板节点不存在，无法导出abc：{}".format(node_full))
                    continue
                node = pm.PyNode(node_full)
                if node.getShape() and node.getShape().type() == "camera":
                    node.setAttr("overscan", 1.0)

                abc_path = v_dir_abc + '/' + abc_name
                pm.AbcExport(
                    j="-frameRange 1 50 -uvWrite -writeColorSets -worldSpace -dataFormat ogawa -root " + node_full + " -file " + abc_path
                )

        if pm:
            utils.executeInMainThreadWithResult(process)


    except Exception:
        return traceback.format_exc()
