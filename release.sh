#!/bin/bash
set -euo pipefail

PLUGIN_JSON="$(dirname "$0")/.claude-plugin/plugin.json"

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

sed -i "s/\"version\": *\"$current\"/\"version\": \"$next\"/" "$PLUGIN_JSON"

echo "$current -> $next"

cd "$(dirname "$0")"
git add .claude-plugin/plugin.json
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

claude plugin update doc-agent@local

echo "Released $next"
