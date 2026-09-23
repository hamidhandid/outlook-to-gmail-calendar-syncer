from __future__ import annotations


def run_gui() -> None:
    """Open the CustomTkinter app. Requires Tk (Homebrew: brew install python-tk@3.13)."""
    try:
        import tkinter  # noqa: F401
        import customtkinter  # noqa: F401
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "GUI needs Tk + customtkinter.\n"
            "\n"
            "On Homebrew Python:\n"
            "  brew install python-tk@3.13\n"
            "  source .venv/bin/activate\n"
            "  pip install customtkinter\n"
            "\n"
            "Or use the python.org macOS installer (includes Tk), recreate the venv, then:\n"
            "  pip install -r requirements.txt\n"
            "\n"
            f"Detail: {exc}"
        ) from exc

    from .gui_app import run_gui as _run

    _run()
