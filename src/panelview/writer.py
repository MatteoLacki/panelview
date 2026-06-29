from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from panelview.panel import ProcessPanel


class PanelWriter:
    """Feed output to a passive ProcessPanel from any background thread."""

    def __init__(self, panel: ProcessPanel, app) -> None:
        self._panel = panel
        self._app = app

    def write(self, stream: str, line: str) -> None:
        """Write one line to 'stdout' or 'stderr'. Thread-safe."""
        self._app.call_from_thread(self._panel._write_line_safe, stream, line)

    def close(self, returncode: int) -> None:
        """Signal that the associated process has finished. Thread-safe."""
        self._app.call_from_thread(self._panel._set_done, returncode)
