#!/usr/bin/env python3
"""PreToolUse hook: block Read access to files matching block-list patterns.

Reads tool input JSON from stdin, checks file_path against glob patterns
in .doc-agents/block-list.json. Exits 2 (block) if matched, 0 (allow) otherwise.
"""

import fnmatch
import json
import os
import sys


def main():
    # Parse tool input from stdin
    try:
        tool_input = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    file_path = tool_input.get("tool_input", {}).get("file_path", "")
    if not file_path:
        sys.exit(0)

    # Load block list from project root (cwd)
    block_list_path = os.path.join(os.getcwd(), ".doc-agents", "block-list.json")
    try:
        with open(block_list_path) as f:
            block_list = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        sys.exit(0)

    patterns = block_list.get("patterns", [])
    if not patterns:
        sys.exit(0)

    # Normalize file_path: make relative to cwd if absolute
    cwd = os.getcwd()
    if os.path.isabs(file_path):
        try:
            file_path = os.path.relpath(file_path, cwd)
        except ValueError:
            # On Windows, relpath can fail across drives
            pass

    # Check each pattern against the file path
    for pattern in patterns:
        # fnmatch doesn't handle ** natively; split pattern on ** segments
        if _glob_match(file_path, pattern):
            print(
                f"BLOCKED: '{file_path}' matches block-list pattern '{pattern}'",
                file=sys.stderr,
            )
            sys.exit(2)

    sys.exit(0)


def _glob_match(path, pattern):
    """Match a file path against a glob pattern with ** support.

    ** matches any number of path segments (including zero).
    * matches within a single segment.
    """
    # Normalize separators
    path = path.replace("\\", "/")
    pattern = pattern.replace("\\", "/")

    # Split into segments
    path_parts = path.split("/")
    pattern_parts = pattern.split("/")

    return _match_segments(path_parts, 0, pattern_parts, 0)


def _match_segments(path_parts, pi, pattern_parts, qi):
    """Recursively match path segments against pattern segments."""
    # Both exhausted: match
    if pi == len(path_parts) and qi == len(pattern_parts):
        return True

    # Pattern exhausted but path remains: no match
    if qi == len(pattern_parts):
        return False

    # ** glob star: try matching 0 or more path segments
    if pattern_parts[qi] == "**":
        # Skip consecutive ** segments
        next_qi = qi + 1
        while next_qi < len(pattern_parts) and pattern_parts[next_qi] == "**":
            next_qi += 1

        # ** at end matches everything remaining
        if next_qi == len(pattern_parts):
            return True

        # Try matching ** against 0, 1, 2, ... path segments
        for skip in range(pi, len(path_parts) + 1):
            if _match_segments(path_parts, skip, pattern_parts, next_qi):
                return True
        return False

    # Path exhausted but pattern remains (and not **): no match
    if pi == len(path_parts):
        return False

    # Regular segment: use fnmatch for wildcards within segment
    if fnmatch.fnmatch(path_parts[pi], pattern_parts[qi]):
        return _match_segments(path_parts, pi + 1, pattern_parts, qi + 1)

    return False


if __name__ == "__main__":
    main()
