from __future__ import annotations

import sys


def main() -> None:
    args = sys.argv[1:]
    if not args:
        print("usage: panelview [-t TITLE] CMD [[-t TITLE] CMD ...]", file=sys.stderr)
        sys.exit(1)
    from panelview import PanelRunner
    runner = PanelRunner()
    i = 0
    while i < len(args):
        if args[i] in ("-t", "--title") and i + 1 < len(args):
            title = args[i + 1]
            i += 2
            if i < len(args):
                runner.add(args[i], title=title)
                i += 1
        else:
            runner.add(args[i])
            i += 1
    runner.run()


if __name__ == "__main__":
    main()
