"""
Live demo: simulates a small pipeline where new jobs spawn as earlier ones finish.

    stage-1a ─┐
               ├─▶ stage-2a ─┐
    stage-1b ─┘               ├─▶ stage-3
                   stage-2b ──┘
"""
import time
from panelview import PanelRunner


def pipeline(runner):
    # Stage 1 runs for ~2-3 s; then spawn stage 2 in parallel.
    time.sleep(3.5)
    runner.add_live(
        'for i in 1 2 3 4; do echo "stage-2a: step $i"; sleep 0.5; done',
        title="stage-2a",
    )
    runner.add_live(
        'for i in 1 2 3; do echo "stage-2b: step $i"; sleep 0.7; done',
        title="stage-2b",
    )

    # Stage 2 runs for another ~2-3 s; then spawn the final stage.
    time.sleep(3.5)
    runner.add_live(
        'echo "stage-3: all upstream done"; sleep 1; echo "stage-3: pipeline complete"',
        title="stage-3",
    )


runner = PanelRunner()
runner.add(
    'for i in 1 2 3 4 5; do echo "stage-1a: step $i"; sleep 0.4; done',
    title="stage-1a",
)
runner.add(
    'for i in 1 2 3; do echo "stage-1b: step $i"; sleep 0.6; done',
    title="stage-1b",
)
runner.run_with(pipeline)
