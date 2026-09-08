# -*- coding: utf-8 -*-
import time
import traceback
import maya.utils as maya_utils

from Qt import QtCore, QtWidgets
from publish_gui.ui.theme import STYLESHEET
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED


PROGRESS_UPDATE_INTERVAL = 0.08


def get_app():
    app = QtCore.QCoreApplication.instance()
    if isinstance(app, QtWidgets.QApplication):
        return app
    return None


def is_maya_main_thread():
    app = get_app()
    return app is not None and QtCore.QThread.currentThread() == app.thread()


def run_in_maya_main_thread(func, *args, **kwargs):
    if is_maya_main_thread():
        return func(*args, **kwargs)

    return maya_utils.executeInMainThreadWithResult(
        lambda: func(*args, **kwargs)
    )


def message_dialog(title, message, buttons, parent=None):

    if get_app() is None:
        return None

    def _show():
        msg_box = QtWidgets.QMessageBox(parent)
        msg_box.setStyleSheet(STYLESHEET)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)

        button_map = {}

        for text in buttons:
            btn = msg_box.addButton(
                text,
                QtWidgets.QMessageBox.ActionRole
            )
            button_map[btn] = text

        msg_box.exec_()

        return button_map.get(msg_box.clickedButton())

    return run_in_maya_main_thread(_show)


class ProgressUI(object):

    def __init__(
        self,
        title,
        maximum=1000,
        parent=None,
        enabled=True,
        logger=None
    ):
        self.title = title
        self.maximum = max(1, int(maximum))
        self.parent = parent if isinstance(parent, QtWidgets.QWidget) else None
        self.enabled = enabled
        self.logger = logger

        self.dialog = None
        self.value = 0
        self.text = ""
        self.closed = False

        self.update_queued = False
        self.last_update_time = 0.0

    def _log_error(self):
        if self.logger:
            try:
                self.logger.error(traceback.format_exc())
            except Exception:
                pass

    def _dispatch(self, func):

        if not self.enabled or self.closed or get_app() is None:
            return False

        if is_maya_main_thread():
            func()
        else:
            maya_utils.executeDeferred(func)

        return True

    def _ensure_dialog(self):

        if self.closed or get_app() is None:
            return None

        if self.dialog is not None:
            return self.dialog

        dlg = QtWidgets.QProgressDialog(self.parent)
        dlg.resize(600, 100)
        dlg.setWindowTitle(self.title)
        dlg.setLabelText(self.text or u"处理中...")
        dlg.setRange(0, self.maximum)
        dlg.setValue(self.value)
        dlg.setCancelButton(None)
        dlg.setMinimumDuration(0)
        dlg.setWindowModality(QtCore.Qt.WindowModal)
        dlg.setAutoClose(False)
        dlg.setAutoReset(False)
        dlg.show()
        dlg.raise_()

        self.dialog = dlg

        return dlg

    def show(self, text=u"处理中..."):

        if not self.enabled:
            return

        self.text = text
        self._dispatch(self._ensure_dialog)

    def update(self, value, text=None, force=False):

        if not self.enabled or self.closed:
            return

        self.value = max(0, min(self.maximum, int(value)))

        if text is not None:
            self.text = str(text)

        now = time.time()

        if not force and now - self.last_update_time < PROGRESS_UPDATE_INTERVAL:
            return

        self.last_update_time = now

        if self.update_queued:
            return

        self.update_queued = True

        def _update():

            self.update_queued = False

            if self.closed:
                return

            dlg = self._ensure_dialog()

            if dlg is None:
                return

            dlg.setLabelText(self.text)
            dlg.setValue(self.value)

        if not self._dispatch(_update):
            self.update_queued = False

    def step(self, text=None, amount=1):
        self.update(self.value + amount, text)

    def pump(self):

        if is_maya_main_thread():
            QtCore.QCoreApplication.processEvents()

    def finish(self, text=u"完成"):
        self.update(self.maximum, text, force=True)

    def close(self):

        if self.closed:
            return

        self.closed = True
        self.update_queued = False

        if self.dialog is None:
            return

        def _close():

            if self.dialog is None:
                return

            self.dialog.close()
            self.dialog.deleteLater()
            self.dialog = None

        if is_maya_main_thread():
            _close()
        elif get_app() is not None:
            maya_utils.executeDeferred(_close)


def parallel_map(
    items,
    func,
    workers,
    progress=None,
    progress_start=0,
    progress_end=1000,
    label=None,
    on_result=None
):
    items = list(items)

    if not items:
        return {}

    total = len(items)
    result = {}

    with ThreadPoolExecutor(
        max_workers=min(workers, total)
    ) as executor:

        future_items = {
            executor.submit(func, item): item
            for item in items
        }

        pending = set(future_items)
        done_count = 0

        while pending:

            done_set, pending = wait(
                pending,
                timeout=0.05,
                return_when=FIRST_COMPLETED
            )

            if not done_set:
                if progress:
                    progress.pump()
                continue

            last_item = None

            for future in done_set:

                item = future_items[future]
                value = future.result()

                result[item] = value
                done_count += 1
                last_item = item

                if on_result:
                    on_result(
                        item,
                        value,
                        done_count,
                        total
                    )

            if progress and label:

                value = (
                    progress_start
                    + (progress_end - progress_start)
                    * float(done_count)
                    / float(total)
                )

                progress.update(
                    value,
                    u"{} {}/{}\n{}".format(
                        label,
                        done_count,
                        total,
                        last_item
                    )
                )

    return result
