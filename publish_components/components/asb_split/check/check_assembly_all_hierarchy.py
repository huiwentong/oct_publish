# -*- coding: utf-8 -*-
import traceback

import maya.utils as utils
import pymel.core as pm

from oct.pipeline.task_context import TaskContext

from publish_components.utils.maya_utils import get_asb_nodes


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    检查层级命名规范
    """
    # Assembly 资产顶层层级的命名需是资产的名称。子层的命名前缀，必须是父层级的名称简写。
    # 根层级下只能放子层级组，不能直接挂模型，否则根层级会被当成一个 Prop。
    # 资产类型和是否发布，以 ASB场景拆分管理器 写入的标记为准。
    # 参考: http://wiki.ds.com/pages/viewpage.action?pageId=167379352
    #
    # 本组件是 asb_split 流程的数据种子：往 process_data 写入 asb_root 和 gen_asset_data，
    # 后续的 snapshot_each_object、create_sub_asset_and_record、gen_asb_deadline_job
    # 全部依赖这两个键，runlist 里的先后顺序不能调整。
    try:
        # GUI 模式下 InterFace.init_process_data() 不会被调用，process_data 里没有
        # entity_name / project_id 这些键，实体信息统一从 TaskContext 取。
        # TaskContext 有进程级实例缓存，多个组件重复取几乎没有开销
        tc = TaskContext(process_data['task_id']) or TaskContext.from_env()
        asset_name = tc.entity_name

        # 组件是在 check_panel 的后台线程里跑的，而 Maya API 只能在主线程调用，
        # 直接在这里遍历 DAG 会让 Maya 随机闪退。所有 Maya 操作都收进 check()，
        # 交给 executeInMainThreadWithResult 调度回主线程
        def check():
            asb_root = pm.ls('|{0}'.format(asset_name))
            if not asb_root:
                return u"找不到根层级 |{0} 组".format(asset_name), None, None

            asb_root = asb_root[0]
            if asb_root.type() != 'transform':
                return u"根层级 |{0} 组不是 transform 节点".format(asset_name), None, None

            # 根层级是 Assembly 资产本身，必须是 ASB，下面只能挂子层级组，不能直接挂模型。
            # 否则按“含有 mesh 即为 Prop”的规则，根层级会被判成一个 Prop，
            # 后面拿资产名去建 SG 资产就会撞上 Assembly 资产本身
            if asb_root.getShape():
                return (u"根层级 |{0} 自身带有 shape 节点，根层级必须是一个空的组，"
                        u"请把模型放到子层级组里".format(asset_name)), None, None

            children = asb_root.listRelatives(children=True, type='transform')
            root_meshes = [child.nodeName() for child in children
                           if get_asb_nodes.is_mesh_transform(child)]
            if root_meshes:
                return (u"根层级 |{0} 下直接挂了模型: {1}\n根层级下只能放子层级组，"
                        u"请把这些模型移到对应的子层级组里再发布".format(
                            asset_name, u"、".join(root_meshes))), None, None

            # 命名检查针对全部层级，含标记为不发布的 —— 它们可能是要发布层级的父级，
            # 命名会影响整条路径的校验
            assets_dict_all = get_asb_nodes.get_all_asset_group(group_object=asb_root,
                                                                publish_only=False)
            root_type = assets_dict_all.get(asb_root.longName())
            if root_type != 'ASB':
                return (u"根层级 |{0} 被判定为 {1}，Assembly 资产的根层级必须是 ASB，"
                        u"请检查根层级下的内容和 ASB场景拆分管理器 中的标记".format(
                            asset_name, root_type)), None, None

            for group in assets_dict_all:
                result = get_asb_nodes.check_group_name(longname=group)
                if result is not True:
                    return result, None, None

            # 实际参与发布的层级，已剔除拆分管理器中标记为不发布的层级
            assets_dict = get_asb_nodes.get_all_asset_group(group_object=asb_root)
            if not assets_dict:
                return u"没有任何层级标记为发布，请在 ASB场景拆分管理器 中确认发布标记", None, None

            return None, asb_root, get_asb_nodes.get_gen_asset_data(assets_dict)

        error_msg, asb_root, gen_asset_data = utils.executeInMainThreadWithResult(check)
        if error_msg:
            return error_msg

        # root / geo / high / low 是 maya_gen、mod 那些通用组件约定的键，默认值是
        # 普通资产的 '|Root_grp'。ASB 场景整体就是一个大组，没有 Geo_grp/high/low
        # 分层，所以三者都指向 asb_root（与老 d_assets_info 的写法一致），
        # 否则 check_instanced_node 之类会去找不存在的 |Root_grp。
        # 存 PyNode 而非字符串，与 maya_gen/check_hierarchy_main 保持一致；这些键是
        # 运行期写入的，不会参与 CLI 生成脚本时对 process_data 的 repr
        process_data.update({
            "root": asb_root,
            "geo": asb_root,
            "high": asb_root,
            "gen_asset_data": gen_asset_data,
        })
        # low 这个键不写：ASB 场景没有 low 组。写成 None 的话，下游
        # process_data.get('low', 默认路径) 会拿到 None（.get 的默认值只在键不存在时生效），
        # 再传给 pm.objExists 就是 "Too few arguments given"

        logger.info(u"本次将拆分 {0} 个资产: {1}".format(
            len(gen_asset_data), u"、".join(gen_asset_data.keys())))

    except:
        return traceback.format_exc()
