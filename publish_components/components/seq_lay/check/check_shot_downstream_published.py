# -*- coding: utf-8 -*-
import traceback

from oct.pipeline.shotgun.models import Version


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    已经有 Blocking / 动画 Publish 版本的镜头不允许再从场次 layout 拆分发布
    """
    # 下游已经基于之前的 layout 开始工作，重新拆分会覆盖镜头 layout 并触发缓存 / 镜头 USD 重新导出。
    # 必须放在 check_shot_versions 之后，读它写入的 process_data['linked_task_info']。
    # 报错后在镜头表格里取消勾选这些镜头（CLI 则从 input_form['shots'] 里去掉），不允许跳过。
    try:
        # check_shot_versions 失败时没有 linked_task_info，那边已经报错，这里不重复报
        shots = list(process_data.get('linked_task_info', {}).keys())
        published = {}
        if shots:
            versions = Version.filter(
                filters=[['project', 'name_is', process_data['project_name']],
                         ['entity.Shot.code', 'in', shots],
                         ['sg_task.Task.step.Step.code', 'in', ['Bk', 'An']],
                         ['sg_version_type', 'is', 'Publish']],
                fields=['code'])
            # 版本名格式 {shot}.{step}.{task}.vNNN
            for version in versions:
                published.setdefault(version.code.split('.')[0], []).append(version.code)

        if published:
            return u'以下镜头已有 Blocking / 动画 Publish 版本，不能再参与场次 layout 发布，请取消勾选：\n' + '\n'.join(
                u'{0}: {1}'.format(shot, ', '.join(sorted(codes))) for shot, codes in sorted(published.items()))
    except:
        return traceback.format_exc()
