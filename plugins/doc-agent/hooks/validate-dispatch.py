#!/usr/bin/env python3
"""PreToolUse hook: validate .doc-agents/dispatch.json schema on Write/Edit.

Reads tool input JSON from stdin, checks if file_path targets dispatch.json.
If so, validates the JSON content against the dispatch schema.
Exits 2 (block) if validation fails, 0 (allow) otherwise.
"""

import json
import os
import re
import sys


DISPATCH_ID_RE = re.compile(r"^DOC-[a-z0-9_]+-\d{8}-\d{2}$")
MODULE_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
TARGET_DOC_RE = re.compile(r"^docs/\d{2}-.+\.md$")

REQUIRED_DISPATCH_FIELDS = {
    "dispatch_id": str,
    "module": str,
    "target_doc": str,
    "objective": str,
    "scope_in": list,
    "scope_out": list,
    "required_sections": list,
    "repo_hints": list,
    "canonical_sources": list,
    "consistency_requirements": list,
    "verification_requirements": list,
    "acceptance_criteria": list,
}

# Fields that may be empty arrays
ALLOW_EMPTY = {"canonical_sources", "consistency_requirements"}


def main():
    # Parse tool input from stdin
    try:
        tool_input = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    inner = tool_input.get("tool_input", {})
    file_path = inner.get("file_path", "")
    if not file_path:
        sys.exit(0)

    # Normalize file_path: make relative to cwd if absolute
    cwd = os.getcwd()
    if os.path.isabs(file_path):
        try:
            file_path = os.path.relpath(file_path, cwd)
        except ValueError:
            pass

    # Only validate dispatch.json
    file_path = file_path.replace("\\", "/")
    if not file_path.endswith("dispatch.json"):
        sys.exit(0)

    # Check it's specifically .doc-agents/dispatch.json
    if file_path != ".doc-agents/dispatch.json" and not file_path.endswith(
        "/.doc-agents/dispatch.json"
    ):
        sys.exit(0)

    # Resolve content depending on tool type
    content = inner.get("content")
    if content is None:
        # Edit tool: simulate old_string → new_string replacement
        old_string = inner.get("old_string")
        new_string = inner.get("new_string")
        if old_string is None or new_string is None:
            # Cannot determine final content, allow through
            sys.exit(0)
        dispatch_path = os.path.join(cwd, ".doc-agents", "dispatch.json")
        try:
            with open(dispatch_path) as f:
                existing = f.read()
        except FileNotFoundError:
            # File doesn't exist yet, can't simulate edit
            sys.exit(0)
        content = existing.replace(old_string, new_string, 1)

    # Parse JSON
    try:
        data = json.loads(content)
    except (json.JSONDecodeError, ValueError) as e:
        _block(f"invalid JSON: {e}")

    errors = []

    # Top-level required fields
    if "schema_version" not in data:
        errors.append("$: missing required field 'schema_version'")
    elif not isinstance(data["schema_version"], str):
        errors.append("$.schema_version: must be string")

    if "dispatches" not in data:
        errors.append("$: missing required field 'dispatches'")
        _block_errors(errors)

    dispatches = data["dispatches"]
    if not isinstance(dispatches, list):
        errors.append("$.dispatches: must be array")
        _block_errors(errors)

    if len(dispatches) == 0:
        errors.append("$.dispatches: must be non-empty array")
        _block_errors(errors)

    # Validate optional meta field
    if "meta" in data:
        meta = data["meta"]
        if not isinstance(meta, dict):
            errors.append("$.meta: must be object")

    # Per-dispatch validation
    seen_ids = set()
    seen_modules = set()

    for i, dispatch in enumerate(dispatches):
        prefix = f"$.dispatches[{i}]"

        if not isinstance(dispatch, dict):
            errors.append(f"{prefix}: must be object")
            continue

        # Check required fields and types
        for field, expected_type in REQUIRED_DISPATCH_FIELDS.items():
            if field not in dispatch:
                errors.append(f"{prefix}: missing required field '{field}'")
                continue
            val = dispatch[field]
            if not isinstance(val, expected_type):
                errors.append(
                    f"{prefix}.{field}: must be {expected_type.__name__}"
                )
                continue

            # String fields: check non-empty
            if expected_type is str:
                if field == "objective" and len(val.strip()) < 10:
                    errors.append(
                        f"{prefix}.{field}: must be at least 10 characters"
                    )
                elif field != "objective" and not val.strip():
                    errors.append(f"{prefix}.{field}: must be non-empty string")

            # List fields: check constraints
            if expected_type is list:
                if field not in ALLOW_EMPTY and len(val) == 0:
                    errors.append(f"{prefix}.{field}: must be non-empty array")
                if field == "scope_in" and len(val) > 6:
                    errors.append(
                        f"{prefix}.{field}: must have at most 6 items"
                    )
                # Check all items are non-empty strings
                for j, item in enumerate(val):
                    if not isinstance(item, str) or not item.strip():
                        errors.append(
                            f"{prefix}.{field}[{j}]: must be non-empty string"
                        )

        # Pattern validation for string fields (only if present and correct type)
        if "dispatch_id" in dispatch and isinstance(dispatch["dispatch_id"], str):
            if not DISPATCH_ID_RE.match(dispatch["dispatch_id"]):
                errors.append(
                    f"{prefix}.dispatch_id: must match pattern "
                    "'DOC-[a-z0-9_]+-YYYYMMDD-NN'"
                )

        if "module" in dispatch and isinstance(dispatch["module"], str):
            if not MODULE_RE.match(dispatch["module"]):
                errors.append(
                    f"{prefix}.module: must match pattern '[a-z0-9][a-z0-9_-]*'"
                )

        if "target_doc" in dispatch and isinstance(dispatch["target_doc"], str):
            if not TARGET_DOC_RE.match(dispatch["target_doc"]):
                errors.append(
                    f"{prefix}.target_doc: must match pattern 'docs/NN-name.md'"
                )

    # Cross-dispatch uniqueness
    for i, dispatch in enumerate(dispatches):
        if not isinstance(dispatch, dict):
            continue
        prefix = f"$.dispatches[{i}]"

        did = dispatch.get("dispatch_id")
        if isinstance(did, str) and did:
            if did in seen_ids:
                errors.append(f"{prefix}.dispatch_id: duplicate '{did}'")
            seen_ids.add(did)

        mod = dispatch.get("module")
        if isinstance(mod, str) and mod:
            if mod in seen_modules:
                errors.append(f"{prefix}.module: duplicate '{mod}'")
            seen_modules.add(mod)

    _block_errors(errors)
    sys.exit(0)


def _block(msg):
    """Print error and exit with block code."""
    print(f"BLOCKED: dispatch.json validation failed:\n- {msg}", file=sys.stderr)
    sys.exit(2)


def _block_errors(errors):
    """If errors exist, print them all and exit with block code."""
    if not errors:
        return
    detail = "\n- ".join(errors)
    print(
        f"BLOCKED: dispatch.json validation failed:\n- {detail}",
        file=sys.stderr,
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
