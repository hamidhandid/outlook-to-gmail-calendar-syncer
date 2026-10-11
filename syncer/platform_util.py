from __future__ import annotations

import sys


def is_macos() -> bool:
    return sys.platform == "darwin"


def is_windows() -> bool:
    return sys.platform == "win32"


def is_linux() -> bool:
    return sys.platform.startswith("linux")


def platform_name() -> str:
    if is_macos():
        return "macOS"
    if is_windows():
        return "Windows"
    if is_linux():
        return "Linux"
    return sys.platform


def keyring_store_name() -> str:
    """Human-readable name of the OS secret store used by the keyring package."""
    if is_macos():
        return "macOS Keychain"
    if is_windows():
        return "Windows Credential Manager"
    if is_linux():
        return "the system keyring (Secret Service)"
    return "the system keyring"
