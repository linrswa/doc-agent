#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_JSON="$SCRIPT_DIR/plugins/doc-agent/.claude-plugin/plugin.json"
MARKETPLACE_JSON="$SCRIPT_DIR/.claude-plugin/marketplace.json"

if [[ ! -f "$PLUGIN_JSON" ]]; then
  echo "Error: $PLUGIN_JSON not found"
  exit 1
fi

current=$(grep -o '"version": *"[^"]*"' "$PLUGIN_JSON" | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+')
IFS='.' read -r major minor patch <<< "$current"

case "${1:-}" in
  patch) patch=$((patch + 1)) ;;
  minor) minor=$((minor + 1)); patch=0 ;;
  major) major=$((major + 1)); minor=0; patch=0 ;;
  *)
    echo "Usage: ./release.sh <patch|minor|major>"
    echo "Current version: $current"
    exit 1
    ;;
esac

next="$major.$minor.$patch"

sed -i '' "s/\"version\": *\"$current\"/\"version\": \"$next\"/" "$PLUGIN_JSON"
sed -i '' "s/\"version\": *\"$current\"/\"version\": \"$next\"/" "$MARKETPLACE_JSON"

echo "$current -> $next"

cd "$SCRIPT_DIR"
git add plugins/doc-agent/.claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "chore: bump version to $next"
git tag "v$next"
git push
git push --tags

NOTES_FILE="${2:-}"
if [[ -n "$NOTES_FILE" && -f "$NOTES_FILE" ]]; then
  gh release create "v$next" --title "v$next" --notes-file "$NOTES_FILE"
else
  gh release create "v$next" --title "v$next" --generate-notes
fi

echo "Released $next"
