# coding=utf-8
import traceback

from publish_components.components.maya_shot.process.sub_to_deadline_export_shot_usd import main as submit_animation_shot_usd


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None) -> str | None:
    """提交 Deadline 输出动画镜头 USD（export_shot_usd_ani），供 blk/ani 共用。"""
    try:
        # 局部副本避免把动画导出命令泄漏给其他组件；共用农场配置与错误处理。
        animation_data = dict(process_data, shot_usd_export_command='export_shot_usd_ani')
        result = submit_animation_shot_usd(submit_data, animation_data, parent_widget, logger)
        if result:
            return result
        # 成功自然落到末尾，CLI 拼接后继续执行。
    except Exception:
        return traceback.format_exc()
