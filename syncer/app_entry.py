"""Entry point for the frozen macOS .app (and optional CLI args)."""

from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> None:
    raw = list(sys.argv[1:] if argv is None else argv)
    # Finder may pass -psn_… when the .app is double-clicked.
    args = [a for a in raw if not a.startswith("-psn_")]
    if not args:
        from syncer.gui import run_gui

        run_gui()
        return
    from syncer.__main__ import main as cli_main

    cli_main(args)


if __name__ == "__main__":
    main()
