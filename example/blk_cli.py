# -*- coding: utf-8 -*-
"""
使用项目原生 PublishCli 执行镜头 Blocking 发布。

只需填写下方 MA_FILE / PREVIEW_FILE / PUBLISH_TYPE / IS_SPLIT_TASK，然后运行：

    rez-env oct_publish PySide2 -- python example/blk_cli.py

任务 ID 和版本号由工程文件路径自动解析（见 _cli_common.py 里的路径约定），
Dailies 只跑 runlist 的 Dailies 组：建版本目录、拷预览、创建 SG Version、登记预览 PublishedFile；
Publish 额外执行全部场景检查、发布工程文件 / USD / component 数据，并提交 Deadline 缓存和镜头 USD 输出任务。

注意：这不是 dry-run，运行会写入 ShotGrid 和发布目录；仅导入本文件不会发起发布。
CLI 模式下不执行 Fix，检查项报错即中断。
"""

from publish_core.cli import PublishType

from _cli_common import run_publish


MA_FILE = r"W:/projects/mk2/shot/s99/s990120/blk/maya/s990120.blk.blocking.v006.ma"

PREVIEW_FILE = r"W:/projects/mk2/shot/s99/s990120/blk/maya/s990120.blk.blocking.v001.mov"

# PublishType.DAILY 只提交预览和 SG Version；PublishType.PUBLISH 走完整发布。
PUBLISH_TYPE = PublishType.DAILY

# 是否为拆分任务。blocking 主任务可自由选择；
# 其它任务（如 blocking_a）会由接口强制设为 True，这里填什么都不影响。
IS_SPLIT_TASK = False


def main() -> int:
    """执行非 GUI 发布；成功返回 0，失败返回 1。"""
    return run_publish(
        label="镜头 Blocking",
        ma_file=MA_FILE,
        preview_file=PREVIEW_FILE,
        publish_type=PUBLISH_TYPE,
        extra_form={"is_split_task": IS_SPLIT_TASK},
    )


if __name__ == "__main__":
    raise SystemExit(main())
