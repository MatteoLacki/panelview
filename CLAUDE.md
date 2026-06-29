# panelview — codebase notes

## What it is

Standalone TUI for watching multiple subprocesses in parallel. Each process gets a full-window browser-style tab. Built on [textual](https://github.com/Textualize/textual) 8.x.

## File map

| File | Role |
|------|------|
| `src/panelview/__init__.py` | `PanelRunner` — public API: `.add(cmd, title)` + `.run()` |
| `src/panelview/app.py` | `PanelApp(App)` — tabbed layout, global key bindings, mode state |
| `src/panelview/panel.py` | `ProcessPanel(Widget)` — one tab per process |
| `src/panelview/signals.py` | `SignalModal`, `CtrlCModal` — modal screens |
| `src/panelview/__main__.py` | CLI: positional args are shell commands; `-t/--title` names a tab |
| `Makefile` | `make venv` (stamp-file, skips if up to date), `make demo`, `make demo-fail` |

## Layout

`TabbedContent` (one `TabPane` per process) fills the screen. `Footer` sits below.

**Critical CSS lesson (textual 8.x):** setting `TabPane { height: 100% }` collapses `ProcessPanel` to zero height because it overrides TabbedContent's internal layout. The correct approach is `TabbedContent { height: 1fr }` and `ProcessPanel { layout: vertical; height: 1fr }` — let TabbedContent handle TabPane sizing itself.

## ProcessPanel internals

- `subprocess.Popen` with separate `stdout=PIPE, stderr=PIPE` (never merged)
- Two daemon threads (`_read_pipe`) feed lines to two `RichLog` widgets via `self.app.call_from_thread(log.write, line)`
- In textual 8.x, `call_from_thread` lives on `App`, not `Widget` — always use `self.app.call_from_thread`
- Widget refs (`_log_stdout`, `_log_stderr`) captured in `on_mount` on the main thread; safe to pass to worker threads
- `active_stream` tracks `"stdout"` | `"stderr"`; the inactive log gets `.hidden` (`display: none`)
- `ProcessPanel.Done(Message)` — posted on process exit; bubbles up to App to update the tab title
- `Message` is imported from `textual.message`, not nested under `Widget` in textual 8.x

## Navigation modes

`PanelApp._mode` (`"tabs"` | `"stream"`) is a plain `str` attribute (not reactive).

- **Tab mode**: `Shift+←/→` calls `Tabs.action_previous_tab()` / `action_next_tab()` via `query_one(TabbedContent).query_one("Tabs")`
- **Stream mode**: same keys call `ProcessPanel.set_stream("stdout"/"stderr")`; entered with `Shift+↓`, exited with `Shift+↑`
- Mode resets to `"tabs"` on `on_tabbed_content_tab_activated`

## Modals

Both live in `signals.py`:

- **`SignalModal`** — lists common Unix signals; `on_list_view_selected` calls `panel.send_signal(sig)`
- **`CtrlCModal`** — three choices: kill current / kill all / kill-all-and-exit; pushed on `Ctrl+C`

## CLI flag

`-t` / `--title` names the next command's tab: `panelview -t name1 cmd1 -t name2 cmd2`.
Without `-t`, tab title defaults to `"Process N"`.
