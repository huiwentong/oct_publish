#!/usr/bin/env python
# -*- coding:utf-8 -*-
import traceback
from collections import defaultdict
import maya.cmds as cmds
import maya.utils as utils
from pathlib import Path


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
贴图文件名相同，但是路径不同
    """
    try:
        def process():
            files = cmds.ls(type="file")
            file_map = defaultdict(list)

            for f in files:
                texture_path = cmds.getAttr(f + ".fileTextureName")
                if not texture_path:
                    continue

                normalized_path = texture_path.replace("\\", "/")
                file_name = Path(texture_path).name
                file_map[file_name].append((f, normalized_path))

            error_nodes = {}
            for file_name, node_list in file_map.items():
                # 提取 node_list 里所有路径
                paths = {path for _, path in node_list}
                if len(paths) > 1:
                    error_nodes[file_name] = node_list

            msg = ""
            if error_nodes:
                msg += "以下材质节点的贴图文件名相同，但是路径不同:\n"

                for file_name, node_list in error_nodes.items():
                    msg += f"  文件名: {file_name}\n"
                    msg += "  涉及节点: "
                    msg += ", ".join([node for node, _ in node_list])
                    msg += "\n\n"

            return msg

        result = utils.executeInMainThreadWithResult(process)
        if result:
            return result

    except:
        return traceback.format_exc()
