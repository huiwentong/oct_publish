# ASB 组装发布

入口为 ASB 资产的 mod/model 任务。支持旧版多 Stage 和新版单 Stage 场景，
发布代码位于 oct_publish 内，不依赖已归档的发布工具。

## 数据与顺序

- `check_assets_hierarchy` 确认当前场景与表单文件一致，并写入 `root`、
  `asb_legacy`、`asb_proxy_shapes`。新版要求资产根组下只有一个 USD Stage。
- `check_usd_dirty` 检查新版 root layer，可手动修复保存；旧版保持跳过。
- `check_usd_relative_path` 要求新版引用为 `maya_usd/<工作文件stem>.usda`。
- `collect_asb_comp_data` 写入 `asb_components`，保存子资产引用、变换、可见性。
- `export_asset_ma` 复制 MA 及新版 USD sidecar；贴图由 `copy_scene_images`
  复制到 `sourceimages`，与旧流程一样保留 MA 内的贴图引用。
- `create_asb_usd` 调用共享 `oct.data.usd.step_pub_usds.AsbStepUsd`，生成并检查
  版本 USD、step USD、asb USD、no_tex USD。
- `update_sg_sub_asset` 通过 ORM 创建 Component/ComponentVersion，写入
  `asb_component_links`、`asb_component_version_links`。
- 通用 `create_sg_version` 将刚创建的 Version ID 写入 `sg_version`；
  `link_component_versions` 精确关联这个版本，并保留 Component 的历史版本关联。

Dailies 只执行通用建版本流程，不执行上述组装导出及 Component 关联。
Submit 和 Publish 的组件筛选沿用项目的通用 runlist 规则。

## 执行约束

组件成功时不显式 return，兼容 CLI 将 main 函数体拼接执行的方式。
Maya 场景操作通过主线程调度；纯文件拷贝和 SG 操作留在工作线程。
USD 辅助逻辑位于 `publish_components.utils.maya_utils.asb_build`。

ComponentVersion 的重试复用只覆盖同一 process_data 生命周期；跨进程并发发布
仍需外部任务锁。共享 AsbStepUsd 会更新资产入口 USD，整个文件系统与 SG 发布
不是原子事务，失败后应检查已生成的版本文件和 SG 记录。

隔离回归测试：`python -B -m unittest discover -s test -p test_asb_build.py -v`。
测试不会连接 SG、提交 Deadline 或打开生产 Maya 场景。
