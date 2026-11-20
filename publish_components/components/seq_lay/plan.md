# seq_lay 移植计划

把老工具 `publish_tool/.../depts/mk2/lay_seq` 迁到新架构，做成"整场次批量 layout 发布"组件。只迁 mk2 + Maya 2024，2019 分支全部丢掉。

## 0. 老流程在做什么

场次（Sequence）lay 任务在一个场次 ma 里做完所有镜头，发布分两段：

1. **本地**：发布场次版本（`{seq}.lay.xxx.vNNN`），同时给每个勾选的镜头的 `rough_layout` 任务建版本目录、拷贝拍屏、建无版本号软链、锁目录。
2. **Deadline**（`oct_cache_exporter`，不在本仓库）：
   - `lay_seq_export_fbx`：整场 fbx 导出（`export_seq_fbx.py`）
   - 每个镜头一个 `lay_seq_output_shot_2024` 任务（`lay_seq_output_shot_2024.py`）：从场次 ma 切出镜头 ma、处理 usda、写 `shot_components.json`、建镜头 SG Version + PublishedFile、更新 Shot 的 cut in/out 和 assets、再提镜头的 cache / shot usd 任务。

   参数是 `shot_name ma_file "str(dict(info))"`。脚本实际只读 `version_dir / work_dir / start_f / end_f / v_preview` 这几个字段；老代码传的 `linked_comps / version_dir_no_num / preview` 都没有用到，新组件不再传。镜头 SG Version 名取自 `basename(version_dir)`。

## 1. 路由

`publish_core/cli.py` 里仿照 ASB 的写法加一个分支：

```python
if stepname == 'lay' and self.task_entity.entity.type == 'Sequence':
    stepname = 'seq_lay'
```

已在 SG 上确认：Sequence 的 LAY 是一个独立的 Step（id=2，short_name=`lay`，description=`LAY`），`get_step_short_name` 解析出来是 `lay`，能进这个分支。

路由不能放进 `get_step_short_name`：一是它只拿得到 step，没有实体类型；二是它的返回值就是版本名中间那一段，改成 `seq_lay` 会把场次版本名改坏。

## 2. 两种模式各做什么

| | Dailies | Publish |
|---|---|---|
| 场次版本 | 用户选的串屏 mov 上传到场次 Version | 场次 ma + 预览（没选预览时，用勾选镜头的拍屏拼一个） |
| 镜头 | **什么都不做** | 每个勾选的镜头按它在 SG 上的下一个版本号建目录、拷拍屏、软链、锁目录，再提交 Deadline |
| GUI / CLI | 都支持 | 都支持 |

Dailies 就是普通的发布：`gen/check_selected_preview` + `gen/copy_preview_to_v_dir` + `gen/create_sg_version`。镜头表格只在 Publish 模式下有意义。

## 3. 组件文件

```
seq_lay/
  __init__.py
  interface.py      # CompInterface + 镜头表格 UI
  shots.py          # 扫描场景里的镜头，UI 和 CLI 共用
  runlist.xml
  check/
  process/
```

### shots.py

`scan_shots()`（需要在 Maya 内调用）：

- 数据来自场景里 `ls(type='shot')` 的 `<code>_shot` 节点
- 用 code 到 SG 上找 Shot 和它的 `rough_layout` 任务
- 拍屏默认取该任务工作目录下最新的 `*.v???.mov`
- 返回列表，每项包含 `shot / task_id / sg_ani_cut_in / sg_ani_cut_out / start_f / end_f / preview`

### interface.py

- `submit_form` 只放 `ma_file`。`shots` 放在 `input_form['shots']`，经 `process_data['input_form']` 传给 process。不放进 `submit_form`，是因为 `fill_submit_form` 要求每个字段非空，放进去 CLI 就得每次显式传。实施时确认 GUI 路径下 `process_data` 也带着 `input_form`。
- 镜头表格（只在 Publish 模式下启用）：
  - 列：勾选 / Shot / SG 起止帧 / 场景起止帧 / 拍屏
  - 右键菜单"替换拍屏"
  - 场景里没有对应 shot 节点的镜头不可勾选
  - **不要资产列**：老表格里的资产列只有 2019 版才用；2024 的 Deadline 脚本直接 `ls('*:Root_grp')`
- `tag_list` 和 lay 一样用 `[283, 971, 282]`

### CLI

- `input_form` 可以传 `shots`，只需给 `shot`，可选 `preview`，用来指定发哪些镜头、覆盖哪些拍屏
- 不传 `shots` 时，`check_shot_versions` 在 mayapy 里调 `scan_shots()`，发场景里所有能匹配到 SG 的镜头
- 去掉 `downstream_dcc_only='Maya'` 的限制（它会挡掉无 GUI 的 Publish）；改成在 GUI 模式下检查当前 DCC 是否为 Maya

### runlist.xml

**Dailies 检查**：沿用 lay 的那一组（含 `gen/check_selected_preview`）。

**Publish 检查**（大部分直接复用 `maya_shot` / `maya_gen` 里已有的）：

| 老检查 | 新组件 |
|---|---|
| this_is_maya / check_maya_unit / unknown_plugins / unlock_default_nodes | `maya_gen/generic_check` |
| this_is_picked_file | `maya_shot/check_picked_file_is_current` |
| version_name_match | `maya_gen/check_work_file` |
| check_camera_attrs | `maya_shot/check_camera_attrs` |
| check_hierarchy_seq | `maya_shot/check_shot_hierarchy`（逻辑相同） |
| check_stage_arch_is_new / file_path / content / dirty | `maya_shot/check_stage_*` |
| check_resoucres | `maya_shot/check_resources` |
| check_ref_path | `maya_shot/check_ref_path` |
| nemo_to_maya_rig | `maya_shot/check_nemo_rig` |
| check_omit_asset_gen | `maya_shot/check_omit_asset` |
| check_asset_version | `maya_shot/check_asset_version` |
| check_usd_hierarchy / check_usd_namespace | `maya_shot/check_usd_*` |
| check_abnormal_dag_under_comp | `maya_shot/check_abnormal_dag_under_comp` |
| check_display_layers | `maya_gen/check_display_layers` |
| check_comp_input_source | **迁**到 `seq_lay/check/check_comp_input_source`，测试时再决定去留 |
| （新增） | `seq_lay/check/check_shot_versions`：确定镜头列表（来自 input_form，或者 `scan_shots()`），按每个镜头 SG 上的下一个版本号算出 work_dir / version_dir / v_preview。镜头**工作目录**里已经有同号文件（`{shot}.lay.rough_layout.vNNN.*`）时报错，列出冲突的镜头和文件。新架构的检查项只要报错就会挡住发布，没有跳过开关，所以天然满足"不允许跳过"。通过后写进 `process_data['linked_task_info']` |
| check_preview_files | 重写为 `seq_lay/check/check_shot_previews`：勾选的镜头至少一个；拍屏必须存在，且是正式拍屏工具拍的（读得到 comment）。场次预览没选时不报错，由拼接处理 |
| check_local_image / cache / reference、check_assembly_name | 镜头 lay 迁移时已去掉，跟随 lay 不加 |
| check_shot_asset_hierarchy | 有 `World` 组时直接跳过，mk2 场景都有 World，不迁 |

**Process**（按老顺序，镜头相关的全部 `mode="Publish"`）：

| 老 process | 新组件 |
|---|---|
| clean_scene / clean_ani_scene | `maya_gen/clean_scene`、`maya_shot/clean_ani_scene` |
| collect_linked_task_info | **并入检查** `check_shot_versions`：冲突检查要用到版本号，而检查在 process 之前跑，版本号只能在检查阶段算。实施时确认 GUI 模式下检查写进 `process_data` 的数据 process 也能读到 |
| create_v_dir | `gen/create_v_dir` |
| copy_combined_preview_to_v_dir | Dailies 用 `gen/copy_preview_to_v_dir`；Publish 用 `seq_lay/process/copy_combined_preview`：选了预览就拷贝或转 h264，没选就用 `comp_videos` 拼接勾选镜头的拍屏 |
| copy_resources_to_v_dir | `maya_shot/copy_resources_to_v_dir` |
| delete_nemo_nodes | **不迁**（`check_nemo_rig` 已经要求切回标准 rig；测试时如果发现切换后有 Nemo 残留再加） |
| save_scene / copy_work_file_to_v_dir | `maya_gen/save_scene`、`gen/copy_work_file_to_v_dir` |
| copy_usd_file_to_v_dir / edit_ma_file | `maya_shot/` 同名 |
| create_linked_task_v_dir | `seq_lay/process/`。目录已存在就**报错**，不再 rmtree |
| copy_linked_task_preview | `seq_lay/process/`（只拷贝，不打字幕） |
| export_linked_task_comp_data | 2024 下由 Deadline 生成 `shot_components.json`，不迁 |
| restore_resource_path / save_scene | 复用 |
| sym_link_no_num_version | `gen/` 复用 |
| sym_link_linked_task_no_num_version | `seq_lay/process/` |
| lock_v_dir | `gen/` 复用 |
| lock_linked_task_v_dir | `seq_lay/process/` |
| create_sg_version | `gen/` 复用（场次版本） |
| create_sg_linked_task_version | mk2 已注释掉，由 Deadline 脚本负责，不迁 |
| sub_to_deadline_export_seq_data | `seq_lay/process/`，改用 `oct.pipeline.deadline.CommandLineJob`，只保留 2024 分支 |

镜头 lay runlist 里的 `collect_basic_comp_data / update_sg_version / update_sg_components / sub_to_deadline_cache / sub_to_deadline_export_shot_usd` 是镜头级的，场次版本不加。镜头级的这些工作由 Deadline 的 `lay_seq_output_shot_2024` 完成。

linked_task 系列的 4 个小 process（建目录 / 拷预览 / 软链 / 锁）各自只有十几行，按项目规范保持每个独立一个文件，不合并。

## 4. 已定的决定

1. 只迁 mk2 + Maya 2024
2. Publish 没选场次预览时，拼接镜头拍屏
3. Dailies 只把选的串屏 mov 上传到场次 Version，镜头不做任何事
4. 镜头版本号取每个镜头 SG 上的下一个版本，不跟场次走
5. `check_comp_input_source` 先迁，测试时再定
6. `delete_nemo_nodes` 不迁
7. Publish 同时支持 GUI 和无 GUI 的 CLI
8. Deadline 脚本里镜头工作文件的版本号改为跟随镜头自己的版本（`oct_cache_exporter` 跟随本仓库一起改，见第 5 节）
9. `oct_cache_exporter` 必改 1–3、建议改 4–6 全部做；提交人取发布数据里的 user，不用农场机器的 username
10. 镜头工作目录里已经有同号文件时，由检查项 `check_shot_versions` 报错，不允许跳过

## 5. oct_cache_exporter 的改动

`oct_cache_exporter` 跟随本仓库一起改、一起发版。只动 `lay_seq_output_shot_2024.py`：

- `export_seq_fbx.py` 只读场次 ma 路径，版本名格式没变，**不用改**
- 2019 的 `lay_seq_output_shot.py` 只有老工具在用，**不动**

老 publish_tool 过渡期可能还在用这个脚本，所以下面每一条都要**兼容老工具的调用**。

### 必改

| # | 位置 | 问题 | 改法 |
|---|---|---|---|
| 1 | `:165-174` | 镜头工作文件 `{shot}.lay.rough_layout.vNNN.ma` 和 `maya_usd/*.usda` 的版本号取自场次 ma 文件名，和镜头自己的版本号（决定 4）对不上 | 版本号改从 `info['version_dir']` 末尾的 `.vNNN` 取。老工具传的 version_dir 本来就是场次版本号，所以行为不变 |
| 2 | `:299` | `from tk_oct_publish.proc import images` 引用了**老发布工具**，而且 `images` 根本没用到。老工具一下线，这个 import 就会失败，镜头 SG Version 全部建不出来 | 删掉这行 |
| 3 | `:54-63` `run()` | 异常被 `print_exc` 吞掉，脚本照常退出 0，Deadline 上任务显示成功，但镜头 Version 可能根本没建 | `except` 里 `sys.exit(1)`，让 Deadline 任务标红 |

| 4 | `:494` | SG 的 api_key 明文写在代码里，单独又建了一个 `Shotgun` 连接 | 去掉这段，改用 `octDB.sg` 查 Version。`export_shot_usd.py:402` 和 `octDB.py` 里也有同样的明文 key，不在 seq_lay 范围内，**只记录，不顺手改** |
| 5 | `:316` | `user = get_user(os.environ['username'])`：在 Deadline 节点上取到的是农场机器的运行账号，不是实际提交人 | 提交人从发布数据里取：`process_data['user']`（`gen/create_sg_version` 用的就是它，SG HumanUser 的 tiny dict），经 info 传给脚本直接写进 Version。新组件**必须**传；老工具不传时退回原来的写法，保证兼容 |
| 6 | `:320-338` | 镜头 Version 没有 description 和 tag（2019 版的 `create_sg_linked_task_version` 有，2024 版丢了），`auto_description = 'lay-seq publish'` 这个变量也没用上 | info 里加 `description`（发布填写的说明）和 `tag_id`（发布选择的标签），有就写进 Version。老工具不传，行为不变 |

新组件提交时 info 字段：`version_dir / work_dir / start_f / end_f / v_preview / user / description / tag_id`。

### 拆出来的镜头和标准镜头 lay 发布的对照（已核对，不用补）

| 标准镜头 lay 的 process | 拆出来的镜头由谁做 |
|---|---|
| `sub_to_deadline_cache` | `lay_seq_output_shot_2024` 调 `version_to_deadline2024`，是同一个命令 |
| `sub_to_deadline_export_shot_usd` | `lay_seq_output_shot_2024` 在有 `\|World` 时提交 `export_shot_usd`，是同一个命令 |
| `update_sg_components`（Component / ComponentVersion） | `export_shot_usd.py:324 update_components()` 会写，逻辑相同：`get_or_create_component` + `{prim}.vNNN` 的 ComponentVersion，记录 `sg_master_version` 和 `cache_usd`。标准镜头 lay 其实也是本地写一次、农场再写一次。区别只是时机：要等农场任务跑完才有记录 |
| `update_sg_version`（PublishedFile、帧范围、Shot 的 assets / cut） | `lay_seq_output_shot_2024` 的 `create_sg_task_version()` 都做了，**只少一个预览 mov 的 PublishedFile**。不影响下游，暂不补 |

**结论：拆出来的镜头不需要另外写 Component。**

## 6. 实施记录（实际实现与上文不一致的地方，以这里为准）

1. **场次预览自动拼接（决定 2）**：新框架原本强制要求预览，GUI 的 `publish_form.collect_form_info` 和 CLI 的 `PublishCli.__post_init__` 都会拦下空预览。现在框架这两处改为读组件类上的 `publish_preview_optional` 标记：只有声明了它（目前只有 seq_lay）且不是 Dailies 时才放行，其它环节取默认值 False，行为不变。seq_lay 用自己的 `check_seq_preview` + `copy_seq_preview` 替换 gen 的两个组件：
   - Dailies 必须选一个串屏 mov
   - Publish 选了就用选的，没选就按镜头号顺序拼接各镜头拍屏（`rez-env ffmpeg` 的 concat，直接拷贝码流）
   - 不用 oct_maya 的 `comp_videos`：Dailies 可能在没有 Maya 环境的 cmd 模式下跑
2. **没有单独的 `check_shot_previews`**：老 `check_preview_files` 的正式拍屏 comment 校验只在 Maya ≤ 2020 时执行，2024 下实际只检查文件存在。这个存在性检查已经并进 `check_shot_versions`。
3. **`shots` 的传递方式**：没有走 `process_data['input_form']`。GUI 下 `process_data` 里的 `input_form` 来自 cli，是空的。改为 `CompInterface.fill_submit_form` 把 `input_form['shots']` 写进 `process_data['shots']`，GUI 和 CLI 走同一条路径。CLI 只在非 Dailies 时调 `fill_submit_form`，正好对得上。
4. **保留 `downstream_dcc_only='Maya'`**：它只在 GUI 分支生效，不影响 CLI 的 Publish，所以不用去掉。
5. **`shots.py` 拆成两个函数**：`scan_scene_shots()`（只读 Maya，GUI 检查线程里要放到主线程跑）和 `query_shots()`（查 SG + 找最新拍屏）。
6. **Deadline 镜头任务的 info 写成 JSON 文件**：`write_shot_job_info`（排在 `gen/lock_v_dir` 之前）把所有镜头的 info 写进场次版本目录下的 `seq_lay_shots.json`（`{镜头: info}`，UTF-8，中文原样）。命令行第 3 个参数传这个文件路径，`lay_seq_output_shot_2024.py` 看到 `.json` 结尾就读文件、取 `[shot_name]`，否则按老工具的 `str(dict)` 解析。
   - 不再把 `str(dict)` 拼进命令行：发布注释里的引号 / 换行 / 中文会弄断命令行
   - 试过 base64：`.cmd` 里 `=` 是参数分隔符，引号经 rez-env 转发后保不住，末尾的补位会被截掉，而且内容不方便直接看，已放弃
   - 文件随场次版本归档，可读、可查；在 Deadline 上重新排队也读同一份
7. **传 tag 名 `tag`，不传 `tag_id`**：脚本直接写 `tag_list`，省一次 SG 查询。
8. **Deadline 池子用 `cache`**：沿用 oct_cache_exporter 里"lay/blk/ani 固定 cache"的约定，老代码用的是 `alembic`。
9. **新增检查 `check_shot_downstream_published`**（计划外需求）：镜头已有 Bk / An 的 Publish 版本时不允许参与场次发布，不可跳过。放在 `check_shot_versions` 之后，按 `linked_task_info` 里的镜头一次查完 SG。
10. **拍屏不再拷到镜头工作目录**：`camera_sequencer_creator_2024` 拍屏时已经直接输出到各镜头 rough_layout 的 work 目录（`{镜头}.lay.rough_layout.{场次版本号}.mov`），`copy_linked_task_preview` 只拷到镜头版本目录的 preview 下，给 Deadline 上传 SG 用。`check_shot_versions` 的工作目录冲突检查相应缩小到 Deadline 会写的 `{镜头版本名}.ma` 和 `maya_usd/{镜头版本名}.usda`。
11. **静态自检**：开发期间用过 `test/test_seq_lay_components.py`（组件约束、runlist 引用和顺序、seq_lay_shots.json 往返），提交前已删除。

## 7. 实施顺序

1. 路由 + `interface.py` + `shots.py` + 最小 runlist（Dailies 能跑通场次版本）
2. Publish 检查（几乎全是复用）
3. linked_task 系列 process + 拼接预览
4. `oct_cache_exporter` 改动 + Deadline 提交，用一个测试场次端到端验证镜头 ma / SG Version 的产出；GUI 和 CLI 各跑一遍
5. 两个仓库一起发版
