from __future__ import annotations


class PanelRunner:
    """Collect commands and launch the TUI panel viewer."""

    def __init__(self) -> None:
        self._jobs: list[dict] = []

    def add(self, cmd: str | list, title: str | None = None) -> None:
        self._jobs.append({"cmd": cmd, "title": title})

    def run(self) -> None:
        from panelview.app import PanelApp
        PanelApp(self._jobs).run()
