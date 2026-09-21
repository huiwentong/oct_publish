# -*- coding: utf-8 -*-
"""
使用项目原生 PublishCli 执行镜头 Rigging 发布。

只需填写下方 MA_FILE / PREVIEW_FILE / PUBLISH_TYPE，然后运行：

    rez-env oct_publish PySide2 -- python example/rig_cli.py

任务 ID 和版本号由工程文件路径自动解析（见 _cli_common.py 里的路径约定），
Dailies 只跑 runlist 的 Dailies 组：建版本目录、拷预览、创建 SG Version、登记预览 PublishedFile；
Publish 额外执行全部场景检查、发布工程文件 / USD / component 数据，并提交 Deadline 缓存和镜头 USD 输出任务。

注意：这不是 dry-run，运行会写入 ShotGrid 和发布目录；仅导入本文件不会发起发布。
CLI 模式下不执行 Fix，检查项报错即中断。
"""

from publish_core.cli import PublishType

from _cli_common import run_publish


MA_FILE = r"W:\projects\tdtest\asset\prp\tao_a\rig\maya\tao_a.rig.rigging.v019.ma"

PREVIEW_FILE = r"W:\projects\tdtest\asset\prp\tao_a\rig\maya\tao_a.rig.rigging.v019.png"

# PublishType.DAILY 只提交预览和 SG Version；PublishType.PUBLISH 走完整发布。
PUBLISH_TYPE = PublishType.SUBMIT


def main() -> int:
    """执行非 GUI 发布；成功返回 0，失败返回 1。"""
    return run_publish(
        label="绑定 Rigging",
        ma_file=MA_FILE,
        preview_file=PREVIEW_FILE,
        publish_type=PUBLISH_TYPE,
    )


if __name__ == "__main__":
    raise SystemExit(main())
