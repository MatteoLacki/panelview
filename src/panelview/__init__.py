from __future__ import annotations

import threading
from typing import Callable


class PanelRunner:
    """Collect commands and launch the TUI panel viewer.

    Simple blocking usage (all processes known upfront):

        runner = PanelRunner()
        runner.add("cmd1", title="a")
        runner.add("cmd2", title="b")
        runner.run()

    Dynamic usage (add processes while the TUI is running).
    The TUI *must* stay on the main thread (Python signal constraint), so
    the user's pipeline logic runs in a background thread via run_with():

        def pipeline(add_live):
            time.sleep(2)
            add_live("cmd2", title="second")

        runner = PanelRunner()
        runner.add("cmd1", title="first")
        runner.run_with(pipeline)   # blocks; pipeline runs in background thread
    """

    def __init__(self) -> None:
        self._jobs: list[dict] = []
        self._app = None

    def add(self, cmd: str | list, title: str | None = None) -> None:
        """Register a process before run() / run_with()."""
        self._jobs.append({"cmd": cmd, "title": title})

    def add_live(self, cmd: str | list, title: str | None = None) -> None:
        """Add a new tab while the TUI is running (call from a background thread)."""
        if self._app is None:
            raise RuntimeError("add_live() called before TUI started.")
        self._app.call_from_thread(self._app.add_process, cmd, title)

    def run(self) -> None:
        """Launch the TUI and block until the user closes it."""
        self._run()

    def run_with(self, fn: Callable[["Callable"], None]) -> None:
        """Launch the TUI on the main thread; run fn(add_live) in a background thread.

        fn receives a single argument: the add_live() callable.
        The TUI closes when the user quits (Ctrl+C / Ctrl+X all tabs).
        """
        def _bg():
            fn(self.add_live)

        self._run(ready_callback=lambda: threading.Thread(target=_bg, daemon=True).start())

    def _run(self, ready_callback=None) -> None:
        from panelview.app import PanelApp
        self._app = PanelApp(self._jobs, ready_callback=ready_callback)
        self._app.run()
