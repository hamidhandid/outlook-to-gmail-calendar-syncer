from __future__ import annotations

import json
from pathlib import Path

import yaml

from .config import (
    CONFIG_PATH,
    EXAMPLE_PATH,
    ROOT,
    default_config_dict,
    load_settings_dict,
    migrate_legacy_template_defaults,
)

CREDENTIALS_PATH = ROOT / "credentials.json"
TOKEN_PATH = ROOT / "token.json"
CREDENTIALS_PLACEHOLDER_PATH = ROOT / "credentials.PLACEHOLDER.json"


def ensure_user_files(*, create_credentials_placeholder: bool = True) -> list[str]:
    """Create missing local files a first-time user needs.

    - config.yaml: created from defaults / example
    - credentials.json: cannot invent a real Google OAuth client; optionally write a
      clearly named PLACEHOLDER the user replaces after Google Cloud setup
    - token.json: created automatically after the first successful Google sign-in
      (not created empty here)

    Returns human-readable notes about what was created.
    """
    notes: list[str] = []
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT / "logs").mkdir(exist_ok=True)

    if not CONFIG_PATH.exists():
        # Prefer programmatic defaults so Digikala-oriented values always apply.
        CONFIG_PATH.write_text(
            yaml.safe_dump(default_config_dict(), sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        if EXAMPLE_PATH.exists():
            notes.append(f"Created {CONFIG_PATH.name} with current defaults")
        else:
            notes.append(f"Created {CONFIG_PATH.name} with defaults")
    else:
        _ = load_settings_dict(CONFIG_PATH)
        notes.extend(migrate_legacy_template_defaults(CONFIG_PATH))

    notes.append(f"Data folder: {ROOT}")

    if not CREDENTIALS_PATH.exists() and create_credentials_placeholder:
        if not CREDENTIALS_PLACEHOLDER_PATH.exists():
            CREDENTIALS_PLACEHOLDER_PATH.write_text(
                json.dumps(
                    {
                        "_comment": (
                            "This is NOT a working Google OAuth client. "
                            "Use Setup Google / Import credentials in the app, "
                            "then save the real Desktop client JSON as credentials.json."
                        ),
                        "installed": {
                            "client_id": "REPLACE_ME.apps.googleusercontent.com",
                            "project_id": "replace-me",
                            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                            "token_uri": "https://oauth2.googleapis.com/token",
                            "client_secret": "REPLACE_ME",
                            "redirect_uris": ["http://localhost"],
                        },
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            notes.append(
                f"Created {CREDENTIALS_PLACEHOLDER_PATH.name} — replace with real "
                f"{CREDENTIALS_PATH.name} via Setup Google"
            )
        notes.append(
            f"Missing {CREDENTIALS_PATH.name}. Use Setup Google / Import credentials."
        )

    if not TOKEN_PATH.exists():
        notes.append(
            f"{TOKEN_PATH.name} will be created after the first successful Google sign-in."
        )

    return notes


def data_dir() -> Path:
    return ROOT
