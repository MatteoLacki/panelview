from __future__ import annotations

import signal
import subprocess
import threading
from typing import Any

from textual.app import ComposeResult
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label, RichLog


class ProcessPanel(Widget):
    """Full-window panel: stream bar + scrollable stdout or stderr."""

    CAN_FOCUS = False  # focus goes to the inner RichLog, not the panel itself

    active_stream: reactive[str] = reactive("stdout")

    def __init__(self, cmd: str | list, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._cmd = cmd
        self._proc: subprocess.Popen | None = None
        self._log_stdout: RichLog | None = None
        self._log_stderr: RichLog | None = None

    def compose(self) -> ComposeResult:
        yield Label("", id="stream-bar", classes="hidden")
        yield RichLog(highlight=False, markup=False, wrap=True, id="log-stdout")
        yield RichLog(highlight=False, markup=False, wrap=True, id="log-stderr", classes="hidden")

    def on_mount(self) -> None:
        self._log_stdout = self.query_one("#log-stdout", RichLog)
        self._log_stderr = self.query_one("#log-stderr", RichLog)
        self.run_worker(self._stream_process, thread=True)

    # --- stream mode bar ---

    def set_stream_mode(self, active: bool) -> None:
        bar = self.query_one("#stream-bar", Label)
        if active:
            bar.remove_class("hidden")
            self._update_stream_bar()
        else:
            bar.add_class("hidden")

    def _update_stream_bar(self) -> None:
        try:
            bar = self.query_one("#stream-bar", Label)
            if "hidden" in bar.classes:
                return
            so = "[b]STDOUT[/b]" if self.active_stream == "stdout" else "stdout"
            se = "[b]STDERR[/b]" if self.active_stream == "stderr" else "stderr"
            bar.update(f"← {so}   {se} →    (Shift+↑ to exit)")
        except Exception:
            pass

    # --- stream switching ---

    def set_stream(self, stream: str) -> None:
        self.query_one(f"#log-{self.active_stream}").add_class("hidden")
        self.active_stream = stream
        log = self.query_one(f"#log-{stream}", RichLog)
        log.remove_class("hidden")
        log.focus()
        self._update_stream_bar()

    def focus_log(self) -> None:
        try:
            self.query_one(f"#log-{self.active_stream}", RichLog).focus()
        except Exception:
            pass

    # --- subprocess streaming ---

    def _stream_process(self) -> None:
        # Capture app reference here — we're inside run_worker which has the
        # textual context var set. Child threads we spawn below do not inherit it.
        app = self.app
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
            t_out = threading.Thread(
                target=self._read_pipe, args=(self._proc.stdout, self._log_stdout, app), daemon=True
            )
            t_err = threading.Thread(
                target=self._read_pipe, args=(self._proc.stderr, self._log_stderr, app), daemon=True
            )
            t_out.start()
            t_err.start()
            t_out.join()
            t_err.join()
            self._proc.wait()
            app.call_from_thread(self._set_done, self._proc.returncode)
        except Exception as exc:
            app.call_from_thread(self._notify_error, str(exc))

    def _read_pipe(self, pipe, log: RichLog, app) -> None:
        for line in pipe:
            app.call_from_thread(log.write, line.rstrip("\n"))

    def _set_done(self, returncode: int) -> None:
        # Notify the app to update the tab title.
        self.post_message(self.Done(self, returncode))

    def _notify_error(self, msg: str) -> None:
        self.post_message(self.Done(self, -1))
        try:
            self._log_stderr.write(f"[launch error] {msg}")
        except Exception:
            pass

    # --- public API ---

    def send_signal(self, sig: signal.Signals) -> None:
        if self._proc and self._proc.poll() is None:
            self._proc.send_signal(sig)

    def kill(self) -> None:
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()

    def is_running(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    # --- message ---

    class Done(Message):
        def __init__(self, panel: ProcessPanel, returncode: int) -> None:
            super().__init__()
            self.panel = panel
            self.returncode = returncode
