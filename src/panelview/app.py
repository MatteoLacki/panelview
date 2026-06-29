from __future__ import annotations

from textual.app import App, ComposeResult
from textual.widgets import Footer
from textual.containers import Horizontal

from panelview.panel import ProcessPanel


class PanelApp(App):
    """TUI showing one scrollable panel per subprocess."""

    CSS = """
    Screen {
        layout: vertical;
    }
    Horizontal {
        height: 1fr;
    }
    ProcessPanel {
        width: 1fr;
        height: 1fr;
        border: solid $primary-lighten-2;
        padding: 0;
    }
    ProcessPanel:focus {
        border: solid $accent;
    }
    ProcessPanel.done #title {
        color: $success;
    }
    ProcessPanel.failed #title {
        color: $error;
    }
    #title {
        background: $surface;
        width: 100%;
        padding: 0 1;
    }
    RichLog {
        height: 1fr;
        scrollbar-gutter: stable;
    }
    .hidden {
        display: none;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("tab", "focus_next", "Next panel"),
        ("shift+tab", "focus_previous", "Prev panel"),
    ]

    def __init__(self, jobs: list[dict]) -> None:
        super().__init__()
        self._jobs = jobs

    def compose(self) -> ComposeResult:
        yield Horizontal(
            *[ProcessPanel(j["cmd"], title=j.get("title")) for j in self._jobs]
        )
        yield Footer()

    def on_mount(self) -> None:
        panels = list(self.query(ProcessPanel))
        if panels:
            panels[0].focus()

    def action_quit(self) -> None:
        for panel in self.query(ProcessPanel):
            panel.kill()
        self.exit()
