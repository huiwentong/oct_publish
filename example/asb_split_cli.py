# -*- coding: utf-8 -*-
"""
使用项目原生 PublishCli 执行 ASB 场景拆分发布。

先修改下方示例参数，再运行：

    rez-env oct_publish PySide2 -- python example/asb_split_cli.py

注意：这不是 dry-run。直接运行本文件会执行检查和发布、写入 ShotGrid/发布目录，
并提交 Deadline 任务；仅导入本文件不会发起发布。
"""

from publish_core.cli import PublishCli, PublishType
from publish_core.database.entity import get_user


TASK_ID = 192122

MA_FILE = (
    "W:/projects/tdtest/asset/asb/temp_a_all/mod/maya/temp_a_all.mod.assembly.v006.ma"
)

PREVIEW_FILE = r"W:\projects\tdtest\asset\asb\temp_a_all\mod\maya\temp_a_all.mod.assembly.v004.png"

COMMENT = "使用新的 oct_publish CLI 测试发布真实场景 temp_a_all"

PUBLISH_TAG_ID = 283

VERSION_NUM = 'v006'


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

    publish_cli.log.info("CLI 初始化完成，开始执行 ASB 拆分发布。")
    publish_cli.interface.run_in_cli()

    if publish_cli.interface.all_complete:
        publish_cli.log.info("ASB 拆分发布执行完成。")
        return 0

    publish_cli.log.error("ASB 拆分发布失败，请检查日志。")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
