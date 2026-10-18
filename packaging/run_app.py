"""PyInstaller entry wrapper (absolute imports; not a package relative module)."""

from syncer.app_entry import main

if __name__ == "__main__":
    main()
