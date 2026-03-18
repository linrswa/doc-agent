#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_JSON="$SCRIPT_DIR/plugins/doc-agent/.claude-plugin/plugin.json"
MARKETPLACE_JSON="$SCRIPT_DIR/.claude-plugin/marketplace.json"

usage() {
  cat <<EOF
Usage: ./release.sh <patch|minor|major> [options]

Options:
  -n, --release-note <text>    Inline release notes (multiline supported)
  -f, --release-note-file <f>  Read release notes from file
  --dry-run                    Show what would happen without executing
  -h, --help                   Show this help

Examples:
  ./release.sh minor -n "## Highlights
  - Extract reference docs from SKILL.md
  - Condensed skill files for readability"

  ./release.sh patch -f RELEASE_NOTES.md
  ./release.sh minor                        # auto-generates notes from commits
EOF
}

# --- Parse arguments ---
BUMP=""
NOTES=""
NOTES_FILE=""
DRY_RUN=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    patch|minor|major)
      BUMP="$1"; shift ;;
    -n|--release-note)
      NOTES="${2:?Error: --release-note requires a value}"; shift 2 ;;
    -f|--release-note-file)
      NOTES_FILE="${2:?Error: --release-note-file requires a path}"
      if [[ ! -f "$NOTES_FILE" ]]; then
        echo "Error: file not found: $NOTES_FILE" >&2; exit 1
      fi
      shift 2 ;;
    --dry-run)
      DRY_RUN=true; shift ;;
    -h|--help)
      usage; exit 0 ;;
    *)
      echo "Error: unknown argument '$1'" >&2; usage; exit 1 ;;
  esac
done

if [[ -z "$BUMP" ]]; then
  echo "Error: bump type required (patch|minor|major)" >&2
  usage
  exit 1
fi

# --- Read current version ---
if [[ ! -f "$PLUGIN_JSON" ]]; then
  echo "Error: $PLUGIN_JSON not found" >&2
  exit 1
fi

current=$(grep -o '"version": *"[^"]*"' "$PLUGIN_JSON" | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+')
IFS='.' read -r major minor patch <<< "$current"

case "$BUMP" in
  patch) patch=$((patch + 1)) ;;
  minor) minor=$((minor + 1)); patch=0 ;;
  major) major=$((major + 1)); minor=0; patch=0 ;;
esac

next="$major.$minor.$patch"

echo "Version: $current → $next ($BUMP)"

# --- Build gh release args ---
GH_ARGS=(gh release create "v$next" --title "v$next")

if [[ -n "$NOTES" ]]; then
  GH_ARGS+=(--notes "$NOTES")
elif [[ -n "$NOTES_FILE" ]]; then
  GH_ARGS+=(--notes-file "$NOTES_FILE")
else
  GH_ARGS+=(--generate-notes)
fi

# --- Dry run ---
if $DRY_RUN; then
  echo ""
  echo "[dry-run] Would bump $PLUGIN_JSON to $next"
  echo "[dry-run] Would commit, tag v$next, push"
  echo "[dry-run] Would run: ${GH_ARGS[*]}"
  if [[ -n "$NOTES" ]]; then
    echo "[dry-run] Release notes:"
    echo "$NOTES"
  fi
  exit 0
fi

# --- Execute ---
cd "$SCRIPT_DIR"

sed -i "s/\"version\": *\"$current\"/\"version\": \"$next\"/" "$PLUGIN_JSON"
sed -i "s/\"version\": *\"$current\"/\"version\": \"$next\"/" "$MARKETPLACE_JSON"
git add plugins/doc-agent/.claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "chore: bump version to $next"
git tag "v$next"
git push
git push --tags

"${GH_ARGS[@]}"

REPO_URL="https://github.com/$(gh repo view --json nameWithOwner -q .nameWithOwner)"

claude plugin marketplace update doc-agent
claude plugin update doc-agent@doc-agent

cat <<EOF

Released v$next
$REPO_URL/releases/tag/v$next
EOF
