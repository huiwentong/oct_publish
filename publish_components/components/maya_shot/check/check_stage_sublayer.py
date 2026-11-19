# -*- coding: utf-8 -*-
import traceback
from pathlib import Path

import maya.utils as utils

from oct.pipeline.task_context import TaskContext
from oct_maya.tools.lay.usd_lay_manager_new.core import (
    get_asb_stage_sublayers,
    get_asb_usd_path_mismatch,
    get_asb_version_status,
    get_existing_asb_proxy,
    is_old_asb_architecture,
)
from publish_components.utils.maya_utils import asb_build


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    检查 Bk/An 的 ASB stage 是否为 layout 发布的场景结构：
    必须是 sublayer 引入本镜头 layout 的 asb_all，不能是 layout 的 usda 或别的镜头的文件复制改名，
    且 sublayer 指向的 layout 场景文件必须存在
    """
    # 两个环节的 stage 结构约定不同 (见 usd_utils.get_asb_stage_sublayers):
    #   Lay  : 按资产逐个 reference 组装, root layer 没有 subLayerPaths
    #   Bk/An: 经 load_layout_asb_scene 把 layout 发布的 asb_all 整体以 sublayer 引入,
    #          root layer 一定带 subLayerPaths, 其中应含 {镜头}.asb_all.no_tex.usda
    # 复制改名的文件位置和版本名都对得上, 只有组合弧用错 (reference 而不是 sublayer),
    # check_stage_arch_is_new / check_stage_file_path / check_stage_dirty 都拦不住。
    # check_stage_content 是 Lay 那一侧的判据 (有 subLayers 即报错), 不能给 Bk/An 复用。
    try:
        tc = TaskContext(process_data['task_id'])
        if tc.entity_type != 'Shot':
            return u"当前实体不是镜头：{0}".format(tc.entity_type)
        layout_prefix = '{0}.asb_all'.format(tc.entity_name)

        def check():
            asb_build.init_usd()

            # 旧架构由 check_stage_arch_is_new 负责拦，这里不重复报错
            if is_old_asb_architecture():
                return ""

            # blk/ani 允许整个镜头没有 asb，此时场景里不会有 proxy，
            # 资产该不该有交给 check_sg_component 判断。
            # Lay Manager 在 Bk/An 没有 asb 时会提示「场景里没有 asb」
            # (view.py refresh_asb_version_bar)，那是不阻塞的 UI 提示；
            # 发布检查拦住会堵住没有 asb 的镜头，所以这里有意不跟它一致。
            if not get_existing_asb_proxy():
                return ""

            mismatch = get_asb_usd_path_mismatch()
            if mismatch:
                return (u"stage 引用的 usda 与当前场景不匹配: {0}\n"
                        u"请用 USD Lay Manager 点 \"填入layout场景\" 按钮重新填入".format(mismatch))

            sublayers = get_asb_stage_sublayers()
            if not sublayers:
                return (u"当前 asb 不是 layout 发布的场景结构（stage 没有 subLayers，"
                        u"疑似把 layout 的 usda 复制改名）\n"
                        u"请用 USD Lay Manager 点 \"填入layout场景\" 按钮重新填入")

            layout_sublayers = [p for p in sublayers if Path(p).name.startswith(layout_prefix)]
            if not layout_sublayers:
                return (u"当前 asb 引用的不是本镜头的 layout 场景（疑似复制了别的镜头的文件）: {0}\n"
                        u"应为 {1}.no_tex.usda，请用 USD Lay Manager 点 \"填入layout场景\" 按钮重新填入".format(
                            Path(sublayers[0]).name, layout_prefix))

            # 命名/结构/路径都对，但 sublayer 指向的 layout 场景文件可能不存在 (layout 没输出或被删)，
            # 与 oct_maya 978d5603 (layout动画文件整理) 一致。填入 layout 场景也会失败，所以不提示重新填入。
            # sublayer 可能是相对路径，相对于 usda 所在目录解析；绝对路径拼接后保持不变
            usd_dir = Path(get_asb_version_status()['usd_file'] or '').parent
            missing = [p for p in layout_sublayers if not (usd_dir / p).is_file()]
            if missing:
                return (u"layout 输出的场景文件不存在: {0}\n"
                        u"请联系 layout 环节重新输出，或用 USD Lay Manager 功能集里的 "
                        u"\"生成layout场景(迁移用)\" 生成".format(', '.join(missing)))
            return ""

        result = utils.executeInMainThreadWithResult(check)
        if result:
            return result
    except:
        return traceback.format_exc()
