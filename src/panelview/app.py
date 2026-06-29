from __future__ import annotations

from textual.app import App, ComposeResult
from textual.widgets import Footer, TabbedContent, TabPane

from panelview.panel import ProcessPanel


class PanelApp(App):
    """Browser-style tabbed TUI: one full-window tab per subprocess."""

    CSS = """
    TabbedContent {
        height: 1fr;
    }
    TabPane {
        padding: 0;
    }
    ProcessPanel {
        layout: vertical;
        height: 1fr;
        width: 1fr;
    }
    RichLog {
        height: 1fr;
        scrollbar-gutter: stable;
    }
    .hidden {
        display: none;
    }
    #stream-bar {
        background: $accent-darken-2;
        color: $text;
        width: 100%;
        content-align: center middle;
        height: 1;
    }
    """

    BINDINGS = [
        ("shift+left",  "nav_left",      "Prev"),
        ("shift+right", "nav_right",     "Next"),
        ("shift+down",  "enter_stream",  "Streams"),
        ("shift+up",    "exit_stream",   "Back"),
        ("ctrl+c",      "ctrl_c",        "Signal"),
        ("ctrl+x",      "close_tab",     "Close"),
    ]

    def __init__(self, jobs: list[dict], ready_callback=None) -> None:
        super().__init__()
        self._jobs = jobs
        self._ready_callback = ready_callback
        self._mode = "tabs"   # "tabs" | "stream"
        self._panel_map: dict[str, ProcessPanel] = {}  # tab_id -> panel
        self._counter = 0  # monotonic counter for unique tab/panel IDs

    def _next_ids(self, title: str | None) -> tuple[str, str, str]:
        """Return (tab_id, panel_id, title) and advance counter."""
        i = self._counter
        self._counter += 1
        return f"tab-{i}", f"panel-{i}", title or f"Process {i + 1}"

    def compose(self) -> ComposeResult:
        with TabbedContent():
            for job in self._jobs:
                tab_id, panel_id, title = self._next_ids(job.get("title"))
                with TabPane(title, id=tab_id):
                    yield ProcessPanel(job["cmd"], id=panel_id)
        yield Footer()

    def on_mount(self) -> None:
        for panel in self.query(ProcessPanel):
            tab_id = panel.id.replace("panel-", "tab-", 1)
            self._panel_map[tab_id] = panel
        self._focus_current_log()
        if self._ready_callback:
            self._ready_callback()

    def add_process(self, cmd: str | list, title: str | None = None) -> None:
        """Add a new tab at runtime. Must be called on the main thread."""
        tab_id, panel_id, title = self._next_ids(title)
        panel = ProcessPanel(cmd, id=panel_id)
        self._panel_map[tab_id] = panel
        self.query_one(TabbedContent).add_pane(TabPane(title, panel, id=tab_id))

    # --- tab title updates ---

    def on_process_panel_done(self, event: ProcessPanel.Done) -> None:
        rc = event.returncode
        label = "done" if rc == 0 else f"failed {rc}"
        # Find the tab that owns this panel and update its title.
        tc = self.query_one(TabbedContent)
        for tab_id, panel in self._panel_map.items():
            if panel is event.panel:
                try:
                    tab = tc.get_tab(tab_id)
                    tab.label = f"{tab.label}  [{label}]"
                except Exception:
                    pass
                break

    # --- helpers ---

    def _current_tab_id(self) -> str:
        return self.query_one(TabbedContent).active

    def _current_panel(self) -> ProcessPanel | None:
        return self._panel_map.get(self._current_tab_id())

    def _focus_current_log(self) -> None:
        panel = self._current_panel()
        if panel:
            self.call_later(panel.focus_log)

    # --- actions ---

    def action_nav_left(self) -> None:
        if self._mode == "tabs":
            self.query_one(TabbedContent).query_one("Tabs").action_previous_tab()
            self._focus_current_log()
        else:
            panel = self._current_panel()
            if panel:
                panel.set_stream("stdout")

    def action_nav_right(self) -> None:
        if self._mode == "tabs":
            self.query_one(TabbedContent).query_one("Tabs").action_next_tab()
            self._focus_current_log()
        else:
            panel = self._current_panel()
            if panel:
                panel.set_stream("stderr")

    def action_enter_stream(self) -> None:
        if self._mode == "tabs":
            self._mode = "stream"
            panel = self._current_panel()
            if panel:
                panel.set_stream_mode(True)

    def action_exit_stream(self) -> None:
        if self._mode == "stream":
            self._mode = "tabs"
            panel = self._current_panel()
            if panel:
                panel.set_stream_mode(False)

    def action_ctrl_c(self) -> None:
        from panelview.signals import CtrlCModal
        self.push_screen(CtrlCModal(self._current_panel(), self._panel_map.values()))

    def action_close_tab(self) -> None:
        tab_id = self._current_tab_id()
        panel = self._panel_map.pop(tab_id, None)
        if panel:
            panel.kill()
        self.query_one(TabbedContent).remove_pane(tab_id)
        self._mode = "tabs"

    def on_tabbed_content_tab_activated(self, _) -> None:
        self._mode = "tabs"
        panel = self._current_panel()
        if panel:
            panel.set_stream_mode(False)
        self._focus_current_log()
