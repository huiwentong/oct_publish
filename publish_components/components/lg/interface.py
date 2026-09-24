# -*- coding: utf-8 -*-
from __future__ import annotations
import traceback
from pathlib import Path
from dataclasses import dataclass, field
from publish_components.core import InterFace
from publish_components.utils.lgt_cmp_publish.tags import (
    LEGACY_REVIEW_TAG_IDS,
    configure_required_tag_combo,
)
from publish_components.utils.lgt_cmp_publish.versions import (
    build_form_version_suggestion,
)
from publish_components.utils.lgt_cmp_publish.form import (
    bind_interface_form,
    localize_notify_label,
    reset_nuke_submit_requirements,
)
from publish_components.utils.lgt_cmp_publish.history_ui import install_lgt_cmp_history
from publish_components.utils.lgt_cmp_publish.notify_ui import sort_notify_people
from publish_components.utils.lgt_cmp_publish.cli_adapter import (
    initialize_cli_interface,
)
from publish_components.utils.lgt_cmp_publish.modes import (
    UnsupportedPublishModeError,
    validate_publish_mode,
)
from qtpy import QtWidgets, QtCore, QtGui


class NukeSceneHelper:
    @property
    def current_script_path(self):
        try:
            import nuke
            return nuke.root().name()
        except:
            return ''


class LgtWidget(QtWidgets.QWidget):
    def __init__(self, input_form, parent=None):
        super().__init__(parent)
        self.input_form = input_form
        main_layout = QtWidgets.QVBoxLayout(self)

        self.nk_widget = QtWidgets.QWidget()
        self.select_nk_btn = QtWidgets.QPushButton("选择 Nuke 脚本")
        self.nk_line = QtWidgets.QLineEdit()
        self.nk_line.setReadOnly(True)
        self.nk_pick_btn = QtWidgets.QPushButton("<<")
        nk_layout = QtWidgets.QHBoxLayout()
        nk_layout.addWidget(self.select_nk_btn)
        nk_layout.addWidget(self.nk_line)
        nk_layout.addWidget(self.nk_pick_btn)
        self.nk_widget.setLayout(nk_layout)

        main_layout.addWidget(self.nk_widget)

        self.on_pick_current()
        self.do_connections()

    def do_connections(self):
        self.nk_pick_btn.clicked.connect(self.on_pick_current)
        self.select_nk_btn.clicked.connect(self.on_pick_workfile)

    def on_pick_workfile(self):
        pick_dialog = QtWidgets.QFileDialog()
        pick_dialog.setViewMode(QtWidgets.QFileDialog.Detail)
        pick_dialog.setNameFilters(["Nuke Script(*.nk)"])
        pick_dialog.exec_()

        l_files = pick_dialog.selectedFiles()
        if len(l_files) > 0:
            self.nk_line.setText(l_files[0])
            self.input_form.update({"nk_file": l_files[0]})

    def on_pick_current(self):
        scene_path = NukeSceneHelper().current_script_path
        if scene_path and scene_path != 'Root':
            self.nk_line.setText(scene_path)
            self.input_form.update({"nk_file": scene_path})


class LgtPublishOptionsWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 0)
        self.skip_movie_range_check = QtWidgets.QCheckBox(
            "跳过 MOV 帧数检查"
        )
        self.skip_movie_range_check.setChecked(False)
        self.skip_movie_range_check.setToolTip(
            "默认检查单个 MOV 的帧数是否匹配 ShotGrid Cut 范围；"
            "仅在明确需要时勾选跳过，其他预览检查仍会执行。"
        )
        layout.addWidget(self.skip_movie_range_check)


@dataclass
class CompInterface(InterFace):

    submit_form: dict = field(
        default_factory=lambda: {
            "nk_file": True,
        }
    )

    tag_list: list = field(
        default_factory=lambda: list(LEGACY_REVIEW_TAG_IDS)
    )

    downstream_dcc_only: str | None = 'Nuke'

    def __post_init__(self):
        # These reviewed checks/processes, including the UAT guard, belong to
        # this component. Do not replace them with a database runlist.
        if not self.runlist:
            self.runlist = str(Path(__file__).with_name("runlist.xml"))
        if self.is_gui:
            super().__post_init__()
            return
        initialize_cli_interface(self)

    def gui_pre_interface(self):
        pass

    def init_ui(self, parent: QtWidgets.QWidget):
        # The current LG scope publishes review media only.  The Nuke script
        # remains part of task/context resolution but is not a published
        # source file.  Do not show a selector that implies otherwise.
        self.input_form['nk_file'] = 'default'
        parent.files_group.hide()
        preview_group = parent._preview_list.parentWidget()
        self._publish_options = LgtPublishOptionsWidget(preview_group)
        preview_layout = preview_group.layout()
        left_layout = preview_layout.itemAt(0).layout() if preview_layout else None
        if left_layout is not None:
            # Keep this exceptional bypass visible before the preview image.
            left_layout.insertWidget(0, self._publish_options)
        elif preview_layout is not None:
            preview_layout.addWidget(self._publish_options)
        else:
            raise RuntimeError("LG Form Preview layout is unavailable")

    def gui_post_interface(self):
        localize_notify_label(self.ui_parent)
        sort_notify_people(self.ui_parent, self.task_entity)
        configure_required_tag_combo(self.ui_parent._tag_combo)
        self._configure_publish_mode_ui()
        self.update_version_fields(self.ui_parent)
        install_lgt_cmp_history(self.ui_parent, self.task_entity)

    def _configure_publish_mode_ui(self):
        try:
            validate_publish_mode("lg", self.submit_type)
            return True
        except UnsupportedPublishModeError as exc:
            reason = str(exc)
            for button_name in ("_check_only_btn", "_check_publish_btn"):
                button = getattr(self.ui_parent, button_name, None)
                if button is not None:
                    button.setEnabled(False)
                    button.setToolTip(reason)
            QtCore.QTimer.singleShot(
                0,
                lambda: QtWidgets.QMessageBox.warning(
                    self.ui_parent,
                    "不支持的发布模式",
                    reason,
                ),
            )
            return False

    def fill_submit_form(self):
        try:
            validate_publish_mode("lg", self.submit_type)
        except UnsupportedPublishModeError as exc:
            if self.is_gui and self.ui_parent is not None:
                QtWidgets.QMessageBox.warning(
                    self.ui_parent,
                    "不支持的发布模式",
                    str(exc),
                )
            raise
        options = getattr(self, "_publish_options", None)
        if options is not None:
            skip_movie_range_check = bool(
                options.skip_movie_range_check.isChecked()
            )
        else:
            skip_movie_range_check = self.input_form.get(
                "skip_movie_range_check",
                False,
            )
        self.process_data["skip_movie_range_check"] = skip_movie_range_check
        reset_nuke_submit_requirements(self)
        super().fill_submit_form()
        bind_interface_form(self)

    def update_version_fields(self, parent):
        try:
            scene_path = NukeSceneHelper().current_script_path
            version_codes = self._task_version_codes()
            suggestion = build_form_version_suggestion(
                entity_code=self.task_entity.entity.code,
                step_short_name=self.task_entity.step.short_name,
                task_content=self.task_entity.content,
                script_path=scene_path,
                sg_version_codes=version_codes,
            )
            parent.set_version_name(suggestion.prefix)
            parent._version_edit.setText(suggestion.version_text)
        except:
            print(traceback.format_exc())

    def _task_version_codes(self):
        version_codes = []
        try:
            from publish_core.database.entity import get_history_version
            version_codes.extend(
                row.get("code", "")
                for row in get_history_version(self.task_entity)
            )
        except Exception:
            print(traceback.format_exc())

        if not version_codes:
            try:
                last_version = self.task_entity.sg_last_version
                if last_version:
                    version_codes.append(last_version.code)
            except Exception:
                pass
        return version_codes
