"""Generic background-thread worker.

Every network call, download, or subprocess run in this app is blocking
Python code living in launcher.core / launcher.auth. None of it may run on
the Qt GUI thread or the window will freeze and the OS will flag it as
unresponsive. This module provides one reusable QThread wrapper so each
call site doesn't reinvent thread plumbing.
"""

from __future__ import annotations

import logging
import traceback
from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QObject, QThread, Signal

logger = logging.getLogger(__name__)


class WorkerSignals(QObject):
    finished = Signal(object)  # result
    error = Signal(str, str)  # message, traceback_str
    progress = Signal(str, int, int)  # label, done, total


class Worker(QThread):
    """Runs ``fn(*args, progress_callback=..., **kwargs)`` on a background
    thread. ``fn`` does not need to accept progress_callback if
    ``wants_progress=False``.

    Usage:
        worker = Worker(sync_instance, version, progress=True)
        worker.signals.finished.connect(on_done)
        worker.signals.error.connect(on_error)
        worker.signals.progress.connect(on_progress)
        worker.start()

    Caller must keep a reference to ``worker`` alive until it finishes
    (e.g. as a field on the widget that started it) -- PySide6 will
    silently drop signals from a QThread that's been garbage collected
    mid-run.
    """

    def __init__(
        self,
        fn: Callable[..., Any],
        *args: Any,
        wants_progress: bool = True,
        **kwargs: Any,
    ) -> None:
        super().__init__()
        self.signals = WorkerSignals()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs
        self._wants_progress = wants_progress

    def run(self) -> None:
        try:
            if self._wants_progress:
                self._kwargs.setdefault(
                    "progress",
                    lambda label, done, total: self.signals.progress.emit(
                        label, done, total
                    ),
                )
            result = self._fn(*self._args, **self._kwargs)
        except Exception as exc:  # noqa: BLE001 - must not crash the GUI thread
            logger.exception("Background task failed")
            self.signals.error.emit(str(exc), traceback.format_exc())
        else:
            self.signals.finished.emit(result)
