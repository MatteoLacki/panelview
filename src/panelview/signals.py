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


class SignalModal(ModalScreen):
    """Pop-up list of signals; selecting one sends it to the panel's process."""

    CSS = """
    SignalModal {
        align: center middle;
    }
    #dialog {
        width: 40;
        height: auto;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
    }
    #dialog Label {
        width: 100%;
        text-align: center;
        margin-bottom: 1;
    }
    ListView {
        height: auto;
        max-height: 12;
    }
    """

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
        sig = _signal.Signals(int(event.item.name))
        self._panel.send_signal(sig)
        self.dismiss()
