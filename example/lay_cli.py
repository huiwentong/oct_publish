# -*- coding: utf-8 -*-
"""
使用项目原生 PublishCli 执行镜头 Layout 发布。

先修改下方示例参数，再运行：

    rez-env oct_publish PySide2 -- python example/lay_cli.py

注意：这不是 dry-run。直接运行本文件会执行检查和发布、写入 ShotGrid/发布目录，
并提交 Deadline 任务（缓存输出 + 镜头 USD 输出）；仅导入本文件不会发起发布。
CLI 模式下没有 Fix，检查项报错即中断。
"""

from publish_core.cli import PublishCli, PublishType
from publish_core.database.entity import get_user


TASK_ID = 185527

MA_FILE = r"W:\projects\mk2\shot\s99\s990120\lay\maya\s990120.lay.rough_layout.v013.ma"

PREVIEW_FILE = r"W:\projects\mk2\shot\s99\s990120\lay\maya\s990120.lay.rough_layout.v010.mov"

COMMENT = "使用新的 oct_publish CLI 测试发布镜头 layout s990120"

# 283=正式 971=过程 282=测试
PUBLISH_TAG_ID = 282

VERSION_NUM = 'v013'


def main() -> int:
    """构造 PublishCli 并调用项目已有的非 GUI 发布流程。

    Returns:
        发布子进程成功返回 0，否则返回 1。
    """
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
        input_form={"ma_file": MA_FILE},
    )

    publish_cli.log.info("CLI 初始化完成，开始执行镜头 Layout 发布。")
    publish_cli.interface.run_in_cli()

    if publish_cli.interface.all_complete:
        publish_cli.log.info("镜头 Layout 发布执行完成。")
        return 0

    publish_cli.log.error("镜头 Layout 发布失败，请检查日志。")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
