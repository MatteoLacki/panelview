# panelview

TUI panel viewer for parallel subprocesses. Each process gets its own scrollable panel; navigate between them with the keyboard.

## Install

```bash
make venv
# or manually:
python3 -m venv .venv && .venv/bin/pip install -e .
```

## Try it

```bash
make demo       # three silly processes with mixed stdout/stderr
make demo-fail  # same but one process exits non-zero
```

## Usage

### CLI

Each positional argument is a shell command:

```bash
panelview "cmd1 arg" "cmd2 arg" "cmd3 arg"
```

### Python API

```python
from panelview import PanelRunner

runner = PanelRunner()
runner.add("bwa mem ref.fa reads.fq > out.bam", title="align")
runner.add("featureCounts -a genes.gtf out.bam -o counts.txt", title="count")
runner.run()
```

## Keys

Each process occupies a full-window tab. There are two navigation modes:

**Tab mode** (default)

| Key | Action |
|-----|--------|
| `Shift+←` / `Shift+→` | Switch to previous / next tab |
| `Shift+↓` | Enter stream-select mode for the current tab |
| `↑` `↓` `PgUp` `PgDn` | Scroll output up / down |
| `Ctrl+C` | Open stop menu (kill current / kill all / exit) |
| `Ctrl+X` | Kill current process and close its tab |

**Stream-select mode** (entered with `Shift+↓`)

| Key | Action |
|-----|--------|
| `Shift+←` | Switch to stdout |
| `Shift+→` | Switch to stderr |
| `Shift+↑` | Return to tab mode |

A bar appears at the top of the panel showing which stream is active while in stream-select mode.

## Stop menu (`Ctrl+C`)

Opens a modal with three choices (arrow keys + `Enter` to select, `Escape` to cancel):

- **Send SIGTERM to current process** — politely stop the focused tab's process
- **Send SIGTERM to all processes** — stop everything
- **Kill all and exit** — SIGTERM all processes and quit panelview

## Tab states

Finished processes keep their tab; the tab title gains a suffix:

| Suffix | Meaning |
|--------|---------|
| `[done 0]` | Exited cleanly |
| `[failed N]` | Exited with code N |

## Requirements

- Python 3.11+
- [textual](https://github.com/Textualize/textual) ≥ 0.50
