# -*- coding: utf-8 -*-
"""使用项目原生 ``PublishCli`` 执行 ASB 组装发布。

先填写下方 CLI SETTINGS，再运行：

    rez-env oct_publish PySide2 -- python example/asb_build_cli.py

任务必须是 ASB 资产下的 mod/model 任务，系统才会路由到 asb_build。
这不是 dry-run：脚本会执行检查和发布，并写入 ShotGrid 与发布目录。
"""

import os

from publish_core.cli import PublishCli, PublishType
from publish_core.database.entity import get_user


# -----------------------------------------------------------------------------
# CLI SETTINGS
# -----------------------------------------------------------------------------
TASK_ID = 192132
MA_FILE = r"W:\projects\tdtest\asset\asb\temp_a_all\mod\maya\temp_a_all.mod.model.v009.ma"
PREVIEW_FILE = r"W:\projects\tdtest\asset\asb\temp_a_all\mod\maya\temp_a_all.mod.model.v009.png"
VERSION_NUM = "v009"
COMMENT = "使用 oct_publish CLI 测试 ASB 组装发布流程"

# 283=正式，282=测试。示例默认使用测试标签，确认无误后可改为 283。
PUBLISH_TAG_ID = 282


def _normalize_path(path: str) -> str:
    """Return a forward-slash path accepted by the publish path parser."""
    return path.replace('\\', '/')


def _validate_settings() -> None:
    """在连接发布系统前检查示例中的必填配置。

    Raises:
        ValueError: 任务、版本或文件路径尚未正确填写时。
    """
    if TASK_ID <= 0:
        raise ValueError("请将 TASK_ID 改为 ASB 资产的 mod/model 任务 ID。")
    if not MA_FILE or not os.path.isfile(MA_FILE):
        raise ValueError("MA_FILE 不存在：{}".format(MA_FILE))
    if not PREVIEW_FILE or not os.path.isfile(PREVIEW_FILE):
        raise ValueError("PREVIEW_FILE 不存在：{}".format(PREVIEW_FILE))
    if not VERSION_NUM.startswith("v"):
        raise ValueError("VERSION_NUM 应使用类似 v001 的格式。")


def main() -> int:
    """构造 PublishCli 并执行 ASB 非 GUI 组装发布流程。

    Returns:
        发布子进程成功返回 0，否则返回 1。
    """
    _validate_settings()
    ma_file = _normalize_path(MA_FILE)
    preview_file = _normalize_path(PREVIEW_FILE)
    publish_cli = PublishCli(
        user=get_user(),
        task_id=TASK_ID,
        gui=False,
        publish_type=PublishType.PUBLISH,
        comment=COMMENT,
        publish_tag_id=PUBLISH_TAG_ID,
        version_num=VERSION_NUM,
        dcc="Maya",
        dcc_file=ma_file,
        preview_paths=[preview_file],
        input_form={"ma_file": ma_file},
    )

    publish_cli.log.info("CLI 初始化完成，开始执行 ASB 组装发布。")
    publish_cli.interface.run_in_cli()

    if publish_cli.interface.all_complete:
        publish_cli.log.info("ASB 组装发布执行完成。")
        return 0

    publish_cli.log.error("ASB 组装发布失败，请检查日志。")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
