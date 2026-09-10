# -*- coding: utf-8 -*-
import importlib
import traceback

import maya.cmds as cmds
import maya.utils as utils

from oct.pipeline.shotgun.models import Asset
from oct.pipeline.task_context import TaskContext


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    检查ASB拆分标记
    """
    # 检查 ASB场景拆分管理器 写入的拆分标记：必须有层级标记为发布；要发布的ASB，
    # 它下面的子层级也必须一起发布，否则该ASB的USD组装会缺资产、Deadline的任务依赖也会断开。
    #
    # 同时检查ENV占位：占位组必须是空组，组名必须和SG上的ENV资产对得上。
    # ENV资产还没发布过不算错误，占位会等它发布后自动生效。
    #
    # 发布清单会打印到日志中，发布前可以核对。
    try:
        # GUI 模式下 process_data 里没有 entity_name，实体信息从 TaskContext 取
        tc = TaskContext(process_data['task_id']) or TaskContext.from_env()
        asset_name = tc.entity_name
        root_path = '|{0}'.format(asset_name)

        # 检查主体放在嵌套函数里，main() 只在拿到错误时才 return。
        # CLI 模式下所有组件的 main() 函数体会被平铺进同一个 main()，
        # 在这一层直接 return 会中止整条发布流程，而不只是跳过本组件。
        def check_split_marks():
            # 拆分管理器是可选依赖，没装时本项检查跳过。
            # 这里必须用 importlib 动态导入 —— 组件的 import 会被 AST 提取到 CLI
            # 生成脚本的顶部，写成顶层 import 后即使包了 try/except ImportError，
            # 也会被提成裸 import，在没装该包的机器上生成脚本会直接崩。
            try:
                api = importlib.import_module('oct_maya.tools.mod.asb_split_tool.api')
            except ImportError:
                logger.info(u"没有安装 ASB场景拆分管理器，跳过拆分标记检查")
                return ""

            def check_env_placeholders():
                """检查ENV占位是否可用，并打印本次会组装的ENV清单。

                ENV资产还没有发布过不算错误 —— 占位引用的是不带版本号的 asb usda，
                等资产发布完总ASB打开就有内容了。
                """
                placeholders = api.get_env_placeholders(root_path=root_path,
                                                        publish_only=False)
                if not placeholders:
                    return ""

                errors = []

                # 占位组必须是空组，否则会被当成普通层级拆出来发布
                for longname, env in placeholders.items():
                    if cmds.listRelatives(longname, children=True, fullPath=True):
                        errors.append(u"ENV占位 {0} 里有内容，占位组必须是空组".format(
                            env['asset_name']))

                # 组名和标记里的资产id必须和SG上对得上，组被改过名时会对不上
                asset_ids = [env['asset_id'] for env in placeholders.values()
                             if env['asset_id']]
                sg_assets = {}
                if asset_ids:
                    for sg_asset in Asset.filter(filters=[['id', 'in', asset_ids]]):
                        sg_assets[sg_asset.id] = sg_asset

                used_ids = {}
                for longname, env in placeholders.items():
                    asset_id = env['asset_id']
                    if not asset_id:
                        errors.append(u"ENV占位 {0} 没有记录SG资产id，请在 ASB场景拆分管理器 中"
                                      u"删除后重新添加".format(env['asset_name']))
                        continue

                    sg_asset = sg_assets.get(asset_id)
                    if not sg_asset:
                        errors.append(u"ENV占位 {0} 记录的资产(id={1})在SG上找不到，"
                                      u"请删除后重新添加".format(env['asset_name'], asset_id))
                        continue

                    if sg_asset.code != env['asset_name']:
                        errors.append(u"ENV占位组名 {0} 与SG上的资产名 {1} 不一致，"
                                      u"占位组可能被改过名，请删除后重新添加".format(
                                          env['asset_name'], sg_asset.code))
                    if (sg_asset.sg_asset_type or '').upper() != 'ENV':
                        errors.append(u"ENV占位 {0} 在SG上的资产类型是 {1}，不是 ENV".format(
                            env['asset_name'], sg_asset.sg_asset_type or u'未填写'))

                    if asset_id in used_ids:
                        errors.append(u"ENV占位 {0} 和 {1} 指向同一个资产，请删掉多余的占位".format(
                            env['asset_name'], used_ids[asset_id]))
                    used_ids[asset_id] = env['asset_name']

                if errors:
                    return u"\n".join(errors)

                # 打印本次会组装的ENV，发布前可以核对
                assembled = [env for env in placeholders.values() if env['publish']]
                logger.info(u">>>> 本次会组装 {0} 个ENV资产:".format(len(assembled)))
                for env in assembled:
                    logger.info(u"   {0}  挂在 {1} 下".format(env['asset_name'], env['parent']))

                return ""

            # 要发布的层级
            publish_order = api.get_publish_order(root_path=root_path)
            if not publish_order:
                return u"没有任何层级标记为发布，请在 ASB场景拆分管理器 中点击“取消单独提交”，" \
                       u"或重新指定要单独提交的层级"

            # 要发布的ASB，其子层级必须一起发布
            missing = api.find_unpublished_children(root_path=root_path)
            if missing:
                text = u"以下ASB层级要发布，但它的子层级没有标记发布，请在 ASB场景拆分管理器 中" \
                       u"重新指定单独提交（选中父层级会自动带上子层级）：\n"
                for asb_longname, children in missing.items():
                    child_names = u"、".join(child.split('|')[-1] for child in children)
                    text += u"{0} 缺少: {1}\n".format(asb_longname.split('|')[-1], child_names)
                return text

            # ENV 占位
            env_result = check_env_placeholders()
            if env_result:
                return env_result

            # 打印本次发布清单，方便发布前核对
            logger.info(u">>>> 本次将按以下顺序提交 {0} 个资产:".format(len(publish_order)))
            for index, (longname, asset_type) in enumerate(publish_order, 1):
                logger.info(u"{0}. {1} ({2}) {3}".format(
                    index, longname.split('|')[-1], asset_type, longname))

            return ""

        # 组件跑在 check_panel 的后台线程里，而 api.* 和 cmds.* 都会读场景，
        # Maya API 只能在主线程调用，否则会随机闪退
        result = utils.executeInMainThreadWithResult(check_split_marks)
        if result:
            return result

    except:
        return traceback.format_exc()
