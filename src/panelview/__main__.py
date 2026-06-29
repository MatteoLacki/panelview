from __future__ import annotations

import sys


def main() -> None:
    if not sys.argv[1:]:
        print("usage: panelview CMD [CMD ...]", file=sys.stderr)
        sys.exit(1)
    from panelview import PanelRunner
    runner = PanelRunner()
    for arg in sys.argv[1:]:
        runner.add(arg)
    runner.run()


if __name__ == "__main__":
    main()
