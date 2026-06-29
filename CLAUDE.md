# panelview — codebase notes

## What it is

Standalone TUI for watching multiple subprocesses in parallel panels. Built on [textual](https://github.com/Textualize/textual).

## File map

| File | Role |
|------|------|
| `src/panelview/__init__.py` | `PanelRunner` — public API: `.add(cmd, title)` + `.run()` |
| `src/panelview/app.py` | `PanelApp(App)` — textual app, layout, global key bindings |
| `src/panelview/panel.py` | `ProcessPanel(Widget)` — one panel per process |
| `src/panelview/signals.py` | `SignalModal(ModalScreen)` — signal picker popup |
| `src/panelview/__main__.py` | CLI entry point: each argv is a shell command |
| `Makefile` | `make venv`, `make demo`, `make demo-fail` |

## ProcessPanel internals

- `subprocess.Popen` with **separate** `stdout=PIPE, stderr=PIPE` (not merged)
- Two daemon threads (`_read_pipe`) feed lines into two `RichLog` widgets
- Widget refs captured in `on_mount` (main thread) — passed to threads, written via `call_from_thread`
- `active_stream` reactive (`"stdout"` | `"stderr"`) controls which `RichLog` is visible; the other has CSS class `.hidden` (`display: none`)
- `action_toggle_stream` — bound to `e`
- `action_signal_menu` — bound to `s`; only opens modal if process is still running

## SignalModal

- `ModalScreen` pushed via `self.app.push_screen(SignalModal(panel))`
- Common signals: `SIGINT SIGTERM SIGHUP SIGUSR1 SIGUSR2 SIGKILL SIGSTOP SIGCONT`
- `on_list_view_selected` calls `panel.send_signal(sig)` then `self.dismiss()`
- `Escape` dismisses without sending

## Key bindings

- App-level: `q` quit (kills all procs), `Tab`/`Shift+Tab` focus cycle
- Panel-level (active when panel focused): `e` toggle stream, `s` signal menu

## CSS conventions

- `.hidden { display: none }` — defined in `PanelApp.CSS`, used by stream toggle
- `ProcessPanel.done #title` → `$success` colour
- `ProcessPanel.failed #title` → `$error` colour
- `ProcessPanel:focus` → `$accent` border
