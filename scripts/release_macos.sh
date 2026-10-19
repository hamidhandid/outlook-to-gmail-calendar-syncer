#!/usr/bin/env bash
# Build a macOS DMG and create a GitHub Release for either:
#   - the current VERSION file (new tag), or
#   - an existing previous tag (republish / first-time release for that tag)
#
# Prerequisites (on a Mac):
#   - git remote "origin" pointing at GitHub
#   - gh authenticated:  gh auth login
#   - For a *new* VERSION release: VERSION + CHANGELOG committed on HEAD
#
# Usage (from repo root):
#   ./scripts/release_macos.sh
#   ./scripts/release_macos.sh --draft
#   ./scripts/release_macos.sh --skip-build
#   ./scripts/release_macos.sh --dry-run
#   ./scripts/release_macos.sh --tag v0.7.0          # release that existing tag
#   ./scripts/release_macos.sh --since v0.6.0        # changelog lower bound
#
# Interactive:
#   1) Ask: release current VERSION, or an existing previous tag?
#   2) If previous: pick from the 5 latest tags
#   3) If current VERSION is already tagged: warn and ask whether to continue
#   4) Ask: include changelog since another older tag? (pick from list / only this version)
#
# Output:
#   git tag vX.Y.Z (if new) → pushed to origin if needed
#   GitHub Release vX.Y.Z with dist/Outlook-to-Google-Calendar-Syncer-X.Y.Z.dmg

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

DRAFT=0
SKIP_BUILD=0
DRY_RUN=0
ALLOW_DIRTY=0
RELEASE_TAG=""   # set via --tag or interactive "previous tag"
SINCE_TAG=""
SINCE_SET=0      # 1 if --since was passed (including empty via choice 0 handled later)

usage() {
  awk 'NR==1 {next} /^#/ {sub(/^# ?/, ""); print; next} {exit}' "$0"
  exit "${1:-0}"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --draft) DRAFT=1 ;;
    --skip-build) SKIP_BUILD=1 ;;
    --dry-run) DRY_RUN=1 ;;
    --allow-dirty) ALLOW_DIRTY=1 ;;
    --tag)
      shift
      RELEASE_TAG="${1:-}"
      if [[ -z "$RELEASE_TAG" ]]; then
        echo "ERROR: --tag needs a value like v0.7.0" >&2
        exit 1
      fi
      ;;
    --since)
      shift
      SINCE_TAG="${1:-}"
      SINCE_SET=1
      if [[ -z "$SINCE_TAG" ]]; then
        echo "ERROR: --since needs a tag like v0.6.0" >&2
        exit 1
      fi
      ;;
    -h|--help) usage 0 ;;
    *)
      echo "Unknown option: $1" >&2
      usage 1
      ;;
  esac
  shift
done

run() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "DRY-RUN: $*"
  else
    "$@"
  fi
}

tag_to_version() {
  echo "${1#v}"
}

normalize_tag() {
  local t="$1"
  if [[ "$t" != v* ]]; then
    t="v${t}"
  fi
  echo "$t"
}

ask_yn() {
  # usage: ask_yn "Prompt" default_n|default_y → echoes y or n
  local prompt="$1"
  local def="${2:-n}"
  local hint="y/N"
  [[ "$def" == "y" ]] && hint="Y/n"
  local ans
  read -r -p "$prompt [$hint]: " ans
  ans="$(echo "$ans" | tr '[:upper:]' '[:lower:]')"
  if [[ -z "$ans" ]]; then
    echo "$def"
    return
  fi
  case "$ans" in
    y|yes) echo y ;;
    n|no) echo n ;;
    *) echo "$def" ;;
  esac
}

FILE_VERSION="$(tr -d '[:space:]' < VERSION)"
if [[ ! "$FILE_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "ERROR: VERSION must look like MAJOR.MINOR.PATCH (got: '$FILE_VERSION')" >&2
  exit 1
fi

NOTES_FILE="$(mktemp "${TMPDIR:-/tmp}/syncer-release-notes.XXXXXX")"
cleanup() {
  rm -f "$NOTES_FILE"
}
trap cleanup EXIT

echo "==> VERSION file: $FILE_VERSION"
echo "==> Repo:         $ROOT"

# --- tools -----------------------------------------------------------------
if ! command -v git >/dev/null; then
  echo "ERROR: git is required." >&2
  exit 1
fi
if ! command -v gh >/dev/null; then
  echo "ERROR: GitHub CLI (gh) is required. Install: brew install gh && gh auth login" >&2
  exit 1
fi
if ! gh auth status >/dev/null 2>&1; then
  echo "ERROR: gh is not authenticated. Run: gh auth login" >&2
  exit 1
fi
if [[ "$(uname -s)" != "Darwin" ]] && [[ "$SKIP_BUILD" -eq 0 ]]; then
  echo "ERROR: DMG build requires macOS (or pass --skip-build with an existing DMG)." >&2
  exit 1
fi

LATEST_TAGS=()
while IFS= read -r line; do
  [[ -n "$line" ]] && LATEST_TAGS+=("$line")
done < <(git tag -l 'v*' --sort=-v:refname | head -n 5)

pick_from_latest() {
  # prints selected tag to stdout; prompts on stderr/tty
  local title="$1"
  local allow_none="${2:-0}"  # 1 = offer choice 0 for none
  local i=1
  local choice
  echo >&2
  echo "$title" >&2
  echo >&2
  if [[ ${#LATEST_TAGS[@]} -eq 0 ]]; then
    echo "  (no existing v* tags found)" >&2
  else
    for t in "${LATEST_TAGS[@]}"; do
      printf "  %d) %s\n" "$i" "$t" >&2
      i=$((i + 1))
    done
  fi
  if [[ "$allow_none" -eq 1 ]]; then
    echo "  0) Only this release version (no since-tag)" >&2
  fi
  echo >&2
  while true; do
    if [[ "$allow_none" -eq 1 ]]; then
      read -r -p "Choice [0-${#LATEST_TAGS[@]}]: " choice
    else
      read -r -p "Choice [1-${#LATEST_TAGS[@]}]: " choice
    fi
    if [[ "$choice" =~ ^[0-9]+$ ]]; then
      if [[ "$allow_none" -eq 1 && "$choice" -eq 0 ]]; then
        echo ""
        return
      fi
      if [[ "$choice" -ge 1 && "$choice" -le ${#LATEST_TAGS[@]} ]]; then
        echo "${LATEST_TAGS[$((choice - 1))]}"
        return
      fi
    fi
    echo "Invalid choice." >&2
  done
}

# --- choose release target: current VERSION vs previous tag ----------------
CREATE_NEW_TAG=1
if [[ -n "$RELEASE_TAG" ]]; then
  RELEASE_TAG="$(normalize_tag "$RELEASE_TAG")"
  if ! git rev-parse "$RELEASE_TAG" >/dev/null 2>&1; then
    echo "ERROR: --tag not found locally: $RELEASE_TAG" >&2
    exit 1
  fi
  CREATE_NEW_TAG=0
  VERSION="$(tag_to_version "$RELEASE_TAG")"
  TAG="$RELEASE_TAG"
  echo "==> Releasing existing tag: $TAG"
else
  if [[ ! -t 0 ]]; then
    echo "ERROR: no TTY. Pass --tag vX.Y.Z for a previous tag, or run interactively for current VERSION." >&2
    exit 1
  fi
  echo
  yn="$(ask_yn "Release for a previous tag (not ${FILE_VERSION} / v${FILE_VERSION})?" n)"
  if [[ "$yn" == "y" ]]; then
    if [[ ${#LATEST_TAGS[@]} -eq 0 ]]; then
      echo "ERROR: no previous v* tags to choose from." >&2
      exit 1
    fi
    RELEASE_TAG="$(pick_from_latest "Select which previous tag to release:")"
    CREATE_NEW_TAG=0
    VERSION="$(tag_to_version "$RELEASE_TAG")"
    TAG="$RELEASE_TAG"
    echo "==> Releasing existing tag: $TAG"
  else
    VERSION="$FILE_VERSION"
    TAG="v${VERSION}"
    CREATE_NEW_TAG=1
    echo "==> Releasing current VERSION: $TAG (will create tag if missing)"
  fi
fi

# If releasing current VERSION but that tag already exists, warn and confirm.
if [[ "$CREATE_NEW_TAG" -eq 1 ]]; then
  _tag_local=0
  _tag_remote=0
  git rev-parse "$TAG" >/dev/null 2>&1 && _tag_local=1
  git ls-remote --exit-code --tags origin "refs/tags/$TAG" >/dev/null 2>&1 && _tag_remote=1
  if [[ "$_tag_local" -eq 1 || "$_tag_remote" -eq 1 ]]; then
    echo
    echo "WARNING: tag $TAG already exists (local=$_tag_local remote=$_tag_remote)."
    echo "         VERSION file is $FILE_VERSION — this version was tagged before."
    if [[ ! -t 0 ]]; then
      echo "ERROR: refusing to continue non-interactively. Use --tag $TAG to release that existing tag," >&2
      echo "       or delete the tag first if you intend to recreate it." >&2
      exit 1
    fi
    yn="$(ask_yn "Continue and release using the existing tag $TAG (will not recreate the tag)?" n)"
    if [[ "$yn" != "y" ]]; then
      echo "Aborted."
      exit 1
    fi
    CREATE_NEW_TAG=0
    echo "==> Continuing with existing tag: $TAG"
  fi
fi

DMG_NAME="Outlook-to-Google-Calendar-Syncer-${VERSION}.dmg"
DMG_PATH="$ROOT/dist/$DMG_NAME"

# --- changelog since-tag ---------------------------------------------------
if [[ "$SINCE_SET" -eq 1 ]]; then
  SINCE_TAG="$(normalize_tag "$SINCE_TAG")"
  if ! git rev-parse "$SINCE_TAG" >/dev/null 2>&1; then
    echo "ERROR: --since tag not found: $SINCE_TAG" >&2
    exit 1
  fi
elif [[ -t 0 ]]; then
  echo
  yn="$(ask_yn "Include changelog notes since a previous tag (range down to that tag)?" y)"
  if [[ "$yn" == "y" ]]; then
    if [[ ${#LATEST_TAGS[@]} -eq 0 ]]; then
      echo "WARNING: no tags available; using notes for $VERSION only."
      SINCE_TAG=""
    else
      SINCE_TAG="$(pick_from_latest "Select the older tag (notes go AFTER it, through $TAG):" 1)"
    fi
  else
    SINCE_TAG=""
  fi
else
  SINCE_TAG=""
fi

SINCE_VERSION=""
if [[ -n "$SINCE_TAG" ]]; then
  SINCE_VERSION="$(tag_to_version "$SINCE_TAG")"
  if [[ "$SINCE_VERSION" == "$VERSION" ]]; then
    echo "ERROR: since-tag $SINCE_TAG is the same as the release version $VERSION." >&2
    exit 1
  fi
  echo "==> Since tag: $SINCE_TAG  (notes: after $SINCE_VERSION → through $VERSION)"
else
  echo "==> Since tag: (none) — notes for $VERSION only"
fi

# --- changelog notes -------------------------------------------------------
if ! grep -qE "^## ${VERSION}( |$)" CHANGELOG.md; then
  echo "ERROR: CHANGELOG.md has no section '## ${VERSION}'." >&2
  exit 1
fi
if [[ -n "$SINCE_VERSION" ]] && ! grep -qE "^## ${SINCE_VERSION}( |$)" CHANGELOG.md; then
  echo "ERROR: CHANGELOG.md has no section '## ${SINCE_VERSION}' (from $SINCE_TAG)." >&2
  exit 1
fi

awk -v until_ver="$VERSION" -v since_ver="$SINCE_VERSION" '
  function heading_ver(line) {
    if (match(line, /^## [0-9]+\.[0-9]+\.[0-9]+/)) {
      return substr(line, RSTART + 3, RLENGTH - 3)
    }
    return ""
  }
  {
    v = heading_ver($0)
    if (v != "") {
      if (v == until_ver) { grab = 1 }
      else if (grab && since_ver != "" && v == since_ver) { exit }
      else if (grab && since_ver == "") { exit }
    }
    if (grab) print
  }
' CHANGELOG.md | sed -e 's/[[:space:]]*$//' > "$NOTES_FILE"

python3 - "$NOTES_FILE" <<'PY'
import sys
from pathlib import Path
p = Path(sys.argv[1])
lines = p.read_text().splitlines()
while lines and not lines[0].strip():
    lines.pop(0)
while lines and not lines[-1].strip():
    lines.pop()
p.write_text("\n".join(lines) + ("\n" if lines else ""))
PY

if [[ ! -s "$NOTES_FILE" ]]; then
  echo "ERROR: changelog notes between $VERSION and ${SINCE_VERSION:-<only this>} are empty." >&2
  exit 1
fi

echo "==> Release notes preview:"
sed 's/^/    /' "$NOTES_FILE"
echo

if [[ -t 0 ]]; then
  read -r -p "Continue with tag/build/release? [y/N] " confirm
  case "$confirm" in
    y|Y|yes|YES) ;;
    *)
      echo "Aborted."
      exit 1
      ;;
  esac
fi

# --- git hygiene -----------------------------------------------------------
if [[ -n "$(git status --porcelain)" ]]; then
  if [[ "$ALLOW_DIRTY" -eq 1 ]]; then
    echo "WARNING: working tree is dirty (--allow-dirty)."
  else
    echo "ERROR: working tree is not clean. Commit VERSION/CHANGELOG (and other release files) first," >&2
    echo "       or pass --allow-dirty if you really mean to tag the current HEAD." >&2
    git status -sb >&2
    exit 1
  fi
fi

if [[ "$CREATE_NEW_TAG" -eq 1 ]]; then
  HEAD_VERSION="$(git show HEAD:VERSION 2>/dev/null | tr -d '[:space:]' || true)"
  if [[ -n "$HEAD_VERSION" && "$HEAD_VERSION" != "$VERSION" && "$ALLOW_DIRTY" -eq 0 ]]; then
    echo "ERROR: HEAD has VERSION=$HEAD_VERSION but releasing $VERSION." >&2
    echo "       Commit the VERSION bump before releasing." >&2
    exit 1
  fi
fi

TAG_EXISTS_LOCAL=0
TAG_EXISTS_REMOTE=0
git rev-parse "$TAG" >/dev/null 2>&1 && TAG_EXISTS_LOCAL=1
git ls-remote --exit-code --tags origin "refs/tags/$TAG" >/dev/null 2>&1 && TAG_EXISTS_REMOTE=1

if [[ "$CREATE_NEW_TAG" -eq 1 ]]; then
  # Should be unreachable if the early warning ran; keep as a safety net.
  if [[ "$TAG_EXISTS_LOCAL" -eq 1 || "$TAG_EXISTS_REMOTE" -eq 1 ]]; then
    echo "ERROR: tag $TAG already exists (local=$TAG_EXISTS_LOCAL remote=$TAG_EXISTS_REMOTE)." >&2
    exit 1
  fi
else
  if [[ "$TAG_EXISTS_LOCAL" -eq 0 && "$TAG_EXISTS_REMOTE" -eq 1 ]]; then
    echo "==> Fetching tag $TAG from origin …"
    run git fetch origin "refs/tags/$TAG:refs/tags/$TAG"
    git rev-parse "$TAG" >/dev/null 2>&1 && TAG_EXISTS_LOCAL=1
  fi
  if [[ "$TAG_EXISTS_LOCAL" -eq 0 ]]; then
    echo "ERROR: tag $TAG not found locally (and could not fetch it)." >&2
    exit 1
  fi
fi

if gh release view "$TAG" >/dev/null 2>&1; then
  echo "ERROR: GitHub release $TAG already exists." >&2
  exit 1
fi

# --- tag (new releases only) -----------------------------------------------
if [[ "$CREATE_NEW_TAG" -eq 1 ]]; then
  echo "==> Creating annotated tag $TAG …"
  run git tag -a "$TAG" -m "Release $TAG"
  TAG_EXISTS_LOCAL=1
else
  echo "==> Using existing tag $TAG (not recreating)"
fi

# --- build -----------------------------------------------------------------
if [[ "$SKIP_BUILD" -eq 1 ]]; then
  echo "==> Skipping build (--skip-build)"
else
  echo "==> Building DMG for version $VERSION …"
  if [[ "$VERSION" != "$FILE_VERSION" ]]; then
    echo "    (VERSION file is $FILE_VERSION; overriding DMG version to $VERSION)"
  fi
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "DRY-RUN: VERSION_OVERRIDE=$VERSION ./scripts/build_macos_dmg.sh"
  else
    VERSION_OVERRIDE="$VERSION" ./scripts/build_macos_dmg.sh
  fi
fi

if [[ "$DRY_RUN" -eq 0 ]]; then
  if [[ ! -f "$DMG_PATH" ]]; then
    echo "ERROR: DMG not found: $DMG_PATH" >&2
    echo "       Run without --skip-build, or build first with VERSION_OVERRIDE=$VERSION ./scripts/build_macos_dmg.sh" >&2
    exit 1
  fi
  echo "==> DMG: $DMG_PATH ($(du -h "$DMG_PATH" | awk '{print $1}'))"
fi

# --- push tag if needed + create release -----------------------------------
if [[ "$TAG_EXISTS_REMOTE" -eq 0 ]]; then
  echo "==> Pushing tag $TAG to origin …"
  run git push origin "$TAG"
else
  echo "==> Tag $TAG already on origin (skip push)"
fi

GH_ARGS=(release create "$TAG" --title "$TAG" --notes-file "$NOTES_FILE")
if [[ "$DRAFT" -eq 1 ]]; then
  GH_ARGS+=(--draft)
fi
if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "DRY-RUN: gh ${GH_ARGS[*]} \"$DMG_PATH\""
else
  echo "==> Creating GitHub release $TAG with DMG …"
  gh "${GH_ARGS[@]}" "$DMG_PATH"
fi

echo
echo "Done."
if [[ "$DRY_RUN" -eq 0 ]]; then
  URL="$(gh release view "$TAG" --json url -q .url 2>/dev/null || true)"
  echo "  Tag:     $TAG"
  echo "  DMG:     $DMG_PATH"
  [[ -n "$URL" ]] && echo "  Release: $URL"
fi
