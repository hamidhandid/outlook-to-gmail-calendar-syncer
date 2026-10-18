#!/usr/bin/env bash
# Build a self-contained macOS .app and wrap it in a .dmg.
# Users do NOT need Python installed.
#
# Usage (from repo root):
#   ./scripts/build_macos_dmg.sh
#
# Output:
#   dist/Outlook to Google Calendar Syncer.app
#   dist/Outlook-to-Google-Calendar-Syncer-<version>.dmg

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

VERSION="$(tr -d '[:space:]' < VERSION)"
APP_NAME="Outlook to Google Calendar Syncer"
BIN_NAME="OutlookToGoogleCalendarSyncer"
DMG_NAME="Outlook-to-Google-Calendar-Syncer-${VERSION}.dmg"
DIST_DIR="$ROOT/dist"
BUILD_DIR="$ROOT/build"
STAGE="$(mktemp -d "${TMPDIR:-/tmp}/syncer-dmg.XXXXXX")"

cleanup() {
  rm -rf "$STAGE"
}
trap cleanup EXIT

echo "==> Repo: $ROOT"
echo "==> Version: $VERSION"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This script only builds a macOS .app/.dmg (run it on a Mac)." >&2
  exit 1
fi

PYTHON_BIN="${PYTHON_BIN:-}"
if [[ -z "$PYTHON_BIN" ]]; then
  if [[ -x "$ROOT/.venv/bin/python" ]]; then
    PYTHON_BIN="$ROOT/.venv/bin/python"
  else
    PYTHON_BIN="$(command -v python3)"
  fi
fi

echo "==> Python: $PYTHON_BIN"
"$PYTHON_BIN" -c "import sys; assert sys.version_info >= (3, 11), sys.version"
if ! "$PYTHON_BIN" -c "import _tkinter, tkinter" 2>/dev/null; then
  echo "ERROR: this Python has no Tk (_tkinter)." >&2
  echo "Homebrew:  brew install python-tk@3.11 && recreate the venv with that python3.11" >&2
  echo "Or use the python.org macOS installer (includes Tcl/Tk)." >&2
  exit 1
fi

echo "==> Installing build deps (pyinstaller + requirements)…"
"$PYTHON_BIN" -m pip install -q -r requirements.txt 'pyinstaller>=6.0'

echo "==> Cleaning previous dist/build…"
rm -rf \
  "$DIST_DIR/OutlookToGmailSyncer" \
  "$DIST_DIR/OutlookToGoogleCalendarSyncer" \
  "$DIST_DIR/Outlook to Gmail Syncer.app" \
  "$DIST_DIR/$APP_NAME.app" \
  "$BUILD_DIR"

echo "==> PyInstaller…"
"$PYTHON_BIN" -m PyInstaller --noconfirm --clean packaging/macos.spec

APP_PATH="$DIST_DIR/$APP_NAME.app"
if [[ ! -d "$APP_PATH" ]]; then
  echo "Expected app not found: $APP_PATH" >&2
  ls -la "$DIST_DIR" >&2 || true
  exit 1
fi

echo "==> Staging DMG contents…"
mkdir -p "$STAGE"
cp -R "$APP_PATH" "$STAGE/"
ln -s /Applications "$STAGE/Applications"
cat > "$STAGE/README.txt" <<EOF
Outlook to Google Calendar Syncer ${VERSION}
===========================================

1. Drag "${APP_NAME}.app" into Applications.
2. Open it from Applications (first time: right-click → Open if macOS warns).
3. Use the buttons for setup, get, sync, store, schedule, etc.
   You do NOT need Python installed.

Your config and Google tokens are stored in:
  ~/Library/Application Support/outlook-to-gmail-calendar-syncer/

VPN tip (Iran): personal VPN for Google / first setup; company VPN (or office Wi-Fi) for Exchange.

Optional CLI (same binary, no system Python):
  open -a "${APP_NAME}" --args sync --dry-run
  # or:
  /Applications/${APP_NAME}.app/Contents/MacOS/${BIN_NAME} sync
EOF

echo "==> Creating $DMG_NAME …"
rm -f "$DIST_DIR/$DMG_NAME"
hdiutil create \
  -volname "Outlook to Google Calendar Syncer" \
  -srcfolder "$STAGE" \
  -ov \
  -format UDZO \
  "$DIST_DIR/$DMG_NAME"

echo
echo "Done."
echo "  App: $APP_PATH"
echo "  DMG: $DIST_DIR/$DMG_NAME"
echo
echo "Notarization (optional, for public download):"
echo "  codesign --deep --force --options runtime --sign \"Developer ID Application: …\" \"$APP_PATH\""
echo "  xcrun notarytool submit \"$DIST_DIR/$DMG_NAME\" --keychain-profile \"…\" --wait"
