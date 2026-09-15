# -*- coding: utf-8 -*-
"""
使用项目原生 PublishCli 执行镜头 Blocking 发布。

先核对并修改下方任务、文件路径和版本号，再运行：

    rez-env oct_publish PySide2 -- python example/blk_cli.py

直接运行本文件会执行检查和发布、写入 ShotGrid/发布目录，并提交 Deadline 任务。
仅导入本文件不会发起发布。CLI 模式下不执行 Fix，检查项报错即中断。
"""

from publish_core.cli import PublishCli, PublishType
from publish_core.database.entity import get_user


TASK_ID = 185532

MA_FILE = r"W:/projects/mk2/shot/s99/s990120/blk/maya/s990120.blk.blocking.v006.ma"

# 示例预览路径，请替换为实际文件。
PREVIEW_FILE = r"W:/projects/mk2/shot/s99/s990120/blk/maya/s990120.blk.blocking.v001.mov"

COMMENT = "使用新的 oct_publish CLI 测试发布镜头 blocking s990120"

# 283=正式 971=过程 282=测试
PUBLISH_TAG_ID = 282

# 显式传入带 v 前缀的版本字符串，并与工程文件版本保持一致。
VERSION_NUM = 'v006'

# blocking 主任务可选择是否拆分；非 blocking 任务会由接口强制设为 True。
IS_SPLIT_TASK = False


def main() -> int:
    """执行非 GUI 发布；成功返回 0，失败返回 1。"""
    publish_cli = PublishCli(
        user=get_user(),
        task_id=TASK_ID,
        gui=False,
        publish_type=PublishType.PUBLISH,
        comment=COMMENT,
        publish_tag_id=PUBLISH_TAG_ID,
        version_num=VERSION_NUM,
        dcc="Maya",
        dcc_file=MA_FILE,
        preview_paths=[PREVIEW_FILE],
        input_form={"ma_file": MA_FILE, "is_split_task": IS_SPLIT_TASK},
    )

    publish_cli.log.info("CLI 初始化完成，开始执行镜头 Blocking 发布。")
    publish_cli.interface.run_in_cli()

    if publish_cli.interface.all_complete:
        publish_cli.log.info("镜头 Blocking 发布执行完成。")
        return 0

    publish_cli.log.error("镜头 Blocking 发布失败，请检查日志。")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
