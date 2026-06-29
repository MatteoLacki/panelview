from __future__ import annotations

import signal as _signal
import sys
from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Label, ListView, ListItem

if TYPE_CHECKING:
    from panelview.panel import ProcessPanel

_SIG_NAMES = ["SIGINT", "SIGTERM", "SIGHUP", "SIGUSR1", "SIGUSR2", "SIGKILL"]
if sys.platform != "win32":
    _SIG_NAMES += ["SIGSTOP", "SIGCONT"]

COMMON_SIGNALS: list[_signal.Signals] = [
    getattr(_signal, name) for name in _SIG_NAMES if hasattr(_signal, name)
]

_MODAL_CSS = """
{name} {{
    align: center middle;
}}
#dialog {{
    width: 52;
    height: auto;
    border: thick $accent;
    background: $surface;
    padding: 1 2;
}}
#dialog Label {{
    width: 100%;
    text-align: center;
    margin-bottom: 1;
}}
ListView {{
    height: auto;
    max-height: 14;
}}
"""


class SignalModal(ModalScreen):
    """Pick a signal to send to the current panel's process."""

    CSS = _MODAL_CSS.format(name="SignalModal")
    BINDINGS = [Binding("escape", "dismiss", "Cancel")]

    def __init__(self, panel: ProcessPanel, **kwargs) -> None:
        super().__init__(**kwargs)
        self._panel = panel

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Send signal to process")
            yield ListView(
                *[
                    ListItem(Label(f"{sig.name}  ({sig.value})"), name=str(sig.value))
                    for sig in COMMON_SIGNALS
                ],
                id="sig-list",
            )

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        self._panel.send_signal(_signal.Signals(int(event.item.name)))
        self.dismiss()


class CtrlCModal(ModalScreen):
    """Ctrl+C menu: kill current / kill all / exit."""

    CSS = _MODAL_CSS.format(name="CtrlCModal")
    BINDINGS = [Binding("escape", "dismiss", "Cancel")]

    def __init__(self, current: ProcessPanel | None, all_panels, **kwargs) -> None:
        super().__init__(**kwargs)
        self._current = current
        self._all = list(all_panels)

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("What do you want to do?")
            yield ListView(
                ListItem(Label("Send SIGTERM to current process"), name="kill_current"),
                ListItem(Label("Send SIGTERM to all processes"), name="kill_all"),
                ListItem(Label("Kill all and exit"), name="exit"),
                id="choice-list",
            )

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        choice = event.item.name
        if choice == "kill_current":
            if self._current:
                self._current.send_signal(_signal.SIGTERM)
        elif choice == "kill_all":
            for p in self._all:
                p.send_signal(_signal.SIGTERM)
        elif choice == "exit":
            for p in self._all:
                p.kill()
            self.app.exit()
        self.dismiss()
