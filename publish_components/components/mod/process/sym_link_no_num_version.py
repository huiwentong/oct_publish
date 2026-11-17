# -*- coding:utf-8 -*-
import traceback, shutil
import tempfile
from pathlib import Path
from oct.pipeline import path_acs
from oct.pipeline.task_context import TaskContext


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    记录需要建立链接的 无版本号版本和文件
    """
    try:
        src = process_data['version_dir']
        dst = process_data['version_dir_no_num']
        task_id = process_data.get("task_id")
        tc = TaskContext(task_id) or TaskContext.from_env()
        # TODO 20260910 path_acs 服务器挂载有问题，导致软硬链接失效 暂时先copy， 服务器修复后删除 publish_type 相关即可
        publish_type = process_data.get("publish_type", "")

        def has_publish_v():
            all_versions = tc.task.versions()
            if not all_versions:
                return False
            try:
               tc.task.latest_published_version
               return True
            except:
                return False

        def update_dailies_abcs(src_files, dst_dir):
            if not dst_dir.is_dir():
                path_acs.make_dirs(str(dst_dir))

            staging_dir = Path(tempfile.mkdtemp(prefix="oct-dailies-"))
            backup_dir = dst_dir / "bake_up"
            originals = {}
            written_files = []
            written_backups = []
            keep_staging = False
            try:
                for src_file in src_files:
                    shutil.copy2(src_file, staging_dir / src_file.name)
                    dst_file = dst_dir / src_file.name
                    if dst_file.is_symlink() or dst_file.is_file():
                        snapshot = staging_dir / (src_file.name + ".original")
                        shutil.copy2(dst_file, snapshot, follow_symlinks=False)
                        originals[dst_file] = snapshot
                    elif dst_file.exists():
                        raise OSError(f"ABC 目标路径已被占用：{dst_file}")

                for src_file in src_files:
                    dst_file = dst_dir / src_file.name
                    # A failed copy may have already changed the destination.
                    written_files.append(dst_file)
                    if dst_file.is_symlink():
                        dst_file.unlink()
                    shutil.copy2(staging_dir / src_file.name, dst_file)

                # Keep the first backup and retain each snapshot until the update succeeds.
                for dst_file, snapshot in originals.items():
                    backup_file = backup_dir / dst_file.name
                    if backup_file.exists() or backup_file.is_symlink():
                        continue
                    if not backup_dir.is_dir():
                        path_acs.make_dirs(str(backup_dir))
                    written_backups.append(backup_file)
                    shutil.copy2(snapshot, backup_file, follow_symlinks=False)
            except Exception as error:
                rollback_errors = []
                for dst_file in reversed(written_files):
                    snapshot = originals.get(dst_file)
                    try:
                        if snapshot is None:
                            dst_file.unlink(missing_ok=True)
                        else:
                            if snapshot.is_symlink():
                                dst_file.unlink(missing_ok=True)
                            shutil.copy2(snapshot, dst_file, follow_symlinks=False)
                    except OSError as rollback_error:
                        rollback_errors.append(f"{dst_file}: {rollback_error}")
                for backup_file in reversed(written_backups):
                    try:
                        backup_file.unlink(missing_ok=True)
                    except OSError as rollback_error:
                        rollback_errors.append(f"{backup_file}: {rollback_error}")
                if rollback_errors:
                    keep_staging = True
                    details = "\n".join(rollback_errors)
                    logger.warning(f"更新 ABC 失败：{error}\n恢复失败，本机副本保留在 {staging_dir}\n{details}")
                elif logger is not None:
                    logger.warning(f"更新 ABC 已取消：{error}")

            finally:
                if not keep_staging:
                    shutil.rmtree(staging_dir)

        if publish_type.lower() == 'submit':
            if not Path(dst).exists():
                path_acs.recursive_mkdirs(dst)
            path_acs.unlock_path(dst, True)
            src_p = Path(src)
            dst_p = Path(dst)
            for child in src_p.iterdir():
                dst_child_p = dst_p / child.name

                if dst_child_p.exists():
                    if dst_child_p.is_dir():
                        shutil.rmtree(dst_child_p)
                    else:
                        dst_child_p.unlink()

                if child.is_dir():
                    shutil.copytree(child, dst_child_p)
                else:
                    shutil.copy2(child, dst_child_p)

        elif publish_type.lower() == 'dailies':
            if has_publish_v():
                abc_names = ['camWhole.abc', 'colorpanelsWhole.abc', 'camUpper.abc', 'colorpanelsUpper.abc',
                             'camCloseup.abc', 'colorpanelsCloseup.abc',]
                src_files = [Path(src) / "alembic" / name for name in abc_names]
                missing = [str(src_file) for src_file in src_files if not src_file.is_file()]
                if not missing:
                    path_acs.unlock_path(str(dst), True)
                    try:
                        update_dailies_abcs(src_files, Path(dst) / "alembic")
                    finally:
                        path_acs.lock_path(str(dst), True)
            else:
                logger.warning("当前资产'{}'没有publish 过版本！ 无法链接abc！".format(tc.entity_name))

        else:
            logger.info(str(src))
            logger.info(str(dst))
            path_acs.symlink(src,dst, remove_exists=True)
    except:
        return traceback.format_exc()

