from __future__ import annotations

import signal
import subprocess
import threading
from typing import Any

from textual.app import ComposeResult
from textual.binding import Binding
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label, RichLog


class ProcessPanel(Widget):
    """Single panel: title bar + scrollable stdout or stderr for one subprocess."""

    CAN_FOCUS = True

    BINDINGS = [
        Binding("e", "toggle_stream", "stdout/stderr"),
        Binding("s", "signal_menu", "Send signal"),
    ]

    status: reactive[str] = reactive("starting")
    active_stream: reactive[str] = reactive("stdout")

    def __init__(self, cmd: str | list, title: str | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._cmd = cmd
        self._title = title or (cmd if isinstance(cmd, str) else " ".join(cmd))
        self._proc: subprocess.Popen | None = None
        self._log_stdout: RichLog | None = None
        self._log_stderr: RichLog | None = None

    def compose(self) -> ComposeResult:
        yield Label(self._make_label(), id="title")
        yield RichLog(highlight=False, markup=False, wrap=True, id="log-stdout")
        yield RichLog(highlight=False, markup=False, wrap=True, id="log-stderr", classes="hidden")

    def on_mount(self) -> None:
        # Capture widget refs on the main thread — safe to use from worker threads via call_from_thread.
        self._log_stdout = self.query_one("#log-stdout", RichLog)
        self._log_stderr = self.query_one("#log-stderr", RichLog)
        self.run_worker(self._stream_process, thread=True)

    # --- reactives ---

    def watch_status(self, _: str) -> None:
        self._update_title()

    def watch_active_stream(self, _: str) -> None:
        self._update_title()

    def _update_title(self) -> None:
        try:
            self.query_one("#title", Label).update(self._make_label())
        except Exception:
            pass

    def _make_label(self) -> str:
        return f"[{self.status}] {self._title}  [{self.active_stream}]"

    # --- subprocess streaming ---

    def _stream_process(self) -> None:
        shell = isinstance(self._cmd, str)
        try:
            self._proc = subprocess.Popen(
                self._cmd,
                shell=shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
            self.app.call_from_thread(self._set_status, "running")

            t_out = threading.Thread(
                target=self._read_pipe, args=(self._proc.stdout, self._log_stdout), daemon=True
            )
            t_err = threading.Thread(
                target=self._read_pipe, args=(self._proc.stderr, self._log_stderr), daemon=True
            )
            t_out.start()
            t_err.start()
            t_out.join()
            t_err.join()
            self._proc.wait()
            self.app.call_from_thread(self._set_done, self._proc.returncode)
        except Exception as exc:
            self.app.call_from_thread(self._set_status, f"error: {exc}")

    def _read_pipe(self, pipe, log: RichLog) -> None:
        for line in pipe:
            self.app.call_from_thread(log.write, line.rstrip("\n"))

    # --- actions ---

    def action_toggle_stream(self) -> None:
        other = "stderr" if self.active_stream == "stdout" else "stdout"
        self.query_one(f"#log-{self.active_stream}").add_class("hidden")
        self.query_one(f"#log-{other}").remove_class("hidden")
        self.active_stream = other

    def action_signal_menu(self) -> None:
        if self._proc and self._proc.poll() is None:
            from panelview.signals import SignalModal
            self.app.push_screen(SignalModal(self))

    # --- public API ---

    def send_signal(self, sig: signal.Signals) -> None:
        if self._proc and self._proc.poll() is None:
            self._proc.send_signal(sig)

    def kill(self) -> None:
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()

    # --- state helpers ---

    def _set_status(self, status: str) -> None:
        self.status = status

    def _set_done(self, returncode: int) -> None:
        if returncode == 0:
            self.status = "done 0"
            self.add_class("done")
        else:
            self.status = f"failed {returncode}"
            self.add_class("failed")
