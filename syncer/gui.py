from __future__ import annotations


def run_gui() -> None:
    """Open the CustomTkinter app. Requires Tk + customtkinter on all platforms."""
    try:
        import tkinter  # noqa: F401
        import customtkinter  # noqa: F401
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "GUI needs Tk + customtkinter.\n"
            "\n"
            "macOS (Homebrew Python):\n"
            "  brew install python-tk@3.13\n"
            "  pip install customtkinter\n"
            "\n"
            "Windows (python.org installer): enable Tcl/Tk, then:\n"
            "  pip install -r requirements.txt\n"
            "\n"
            "Linux (Debian/Ubuntu):\n"
            "  sudo apt install python3-tk\n"
            "  pip install -r requirements.txt\n"
            "\n"
            f"Detail: {exc}"
        ) from exc

    from .gui_app import run_gui as _run

    _run()
