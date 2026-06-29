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

| Key | Action |
|-----|--------|
| `Tab` / `Shift+Tab` | Move focus to next / previous panel |
| `↑ ↓ PgUp PgDn` | Scroll within the focused panel |
| `e` | Toggle between stdout and stderr for the focused panel |
| `s` | Open signal menu — send a signal to the focused panel's process |
| `q` | Quit; terminate all running processes |

## Signal menu

Press `s` on any running process to open a list of common signals:
`SIGINT`, `SIGTERM`, `SIGHUP`, `SIGUSR1`, `SIGUSR2`, `SIGKILL`, `SIGSTOP`, `SIGCONT`.
Arrow keys navigate, `Enter` sends, `Escape` cancels.

## Panel states

| State | Meaning |
|-------|---------|
| `[running]` | Process still running |
| `[done 0]` | Exited cleanly |
| `[failed N]` | Exited with code N (title turns red) |
| `[error: ...]` | Failed to launch |

## Requirements

- Python 3.11+
- [textual](https://github.com/Textualize/textual) ≥ 0.50
