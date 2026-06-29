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

        def pipeline(runner):
            time.sleep(2)
            runner.add_live("cmd2", title="second")

        runner = PanelRunner()
        runner.add("cmd1", title="first")
        runner.run_with(pipeline)   # blocks; pipeline(runner) runs in background thread

    For passive panels (output fed externally — e.g. when you already have the process):

        def pipeline(runner):
            writer = runner.add_live_passive(title="my-job")
            writer.write("stdout", "hello from my-job")
            writer.close(0)

        runner.run_with(pipeline)
    """

    def __init__(self) -> None:
        self._jobs: list[dict] = []
        self._app = None

    def add(self, cmd: str | list, title: str | None = None) -> None:
        """Register a process before run() / run_with()."""
        self._jobs.append({"cmd": cmd, "title": title})

    def add_live(self, cmd: str | list, title: str | None = None) -> None:
        """Add a new active tab while the TUI is running. Call from background thread."""
        if self._app is None:
            raise RuntimeError("add_live() called before TUI started.")
        self._app.call_from_thread(self._app.add_process, cmd, title)

    def add_live_passive(self, title: str | None = None) -> "PanelWriter":
        """Add a passive tab and return a PanelWriter for feeding output. Background thread safe."""
        if self._app is None:
            raise RuntimeError("add_live_passive() called before TUI started.")
        return self._app.call_from_thread(self._app.add_passive, title)

    def run(self) -> None:
        """Launch the TUI and block until the user closes it."""
        self._run()

    def run_with(self, fn: Callable[["PanelRunner"], None]) -> None:
        """Launch the TUI on the main thread; run fn(runner) in a background thread.

        fn receives this PanelRunner so it can call add_live / add_live_passive.
        Blocks until the user closes the TUI.
        """
        self._run(ready_callback=lambda: threading.Thread(
            target=lambda: fn(self), daemon=True
        ).start())

    def _run(self, ready_callback=None) -> None:
        from panelview.app import PanelApp
        self._app = PanelApp(self._jobs, ready_callback=ready_callback)
        self._app.run()
