---
name: gen-dispatch
description: "Analyze project structure and generate .doc-agents/dispatch.json — the configuration that drives the doc-agent documentation workflow. Use this skill to initialize or regenerate the dispatch config. Triggers: /gen-dispatch, 'generate dispatch', 'initialize docs config', 'set up documentation system', 'create dispatch config', 'analyze project for docs', 'project structure changed and dispatch is outdated', 'regenerate dispatch templates'. Also triggers when doc-manage detects dispatch.json is missing. Do NOT use for: writing actual documentation (use doc-manage), editing README/CLAUDE.md, or any task that doesn't involve the .doc-agents/dispatch.json config file."
---

# gen-dispatch

Analyze the project and generate `.doc-agents/dispatch.json` — a JSON bundle of dispatch entries for each documentable module. The `validate-dispatch.py` hook validates the JSON on every Write/Edit. doc-manage uses these entries to dispatch tasks to doc-writer.

## Instructions

### Step 0: Load Block List

Read `.doc-agents/block-list.json` (if it exists). Files matching `patterns` array MUST be excluded from `repo_hints`.

### Step 1: Analyze Project Structure

Explore the codebase to identify:

1. **Entry points** — `main()`, `CMakeLists.txt` targets, `package.json` scripts
2. **Module boundaries** — directory structure, namespace/package organization
3. **Communication layers** — API definitions (REST, GraphQL, gRPC), message protocols, IPC
4. **Configuration** — config files, environment variables, settings schemas

### Step 2: Determine Documentation Modules

| Module Type | Purpose |
|-------------|---------|
| architecture | System overview, component relationships |
| protocols | Communication protocols, API specs |
| {component_name} | Individual component documentation |

### Step 3: Generate Dispatch Entries

For each module, generate a dispatch entry. See [references/schema.md](references/schema.md) for the full JSON schema, field constraints, and example output.

### Step 4: Create Task Items

Create Task items for tracking:

1. `TaskCreate` per module with `subject`, `description` (dispatch_id + target_doc + objective), `activeForm`, `metadata.dispatch_id`
2. `TaskUpdate` with `addBlockedBy` for dependency ordering — canonical source modules first

### Step 5: Write Output

Write to `.doc-agents/dispatch.json` (create directory if needed). Execution ordering is managed via Task dependencies, not in the dispatch file.

## Pre-Output Validation

### Block List Filtering

Verify no `repo_hints` paths match block list patterns. Remove any blocked entries.

### Path Existence Verification

Verify all `repo_hints` paths exist with Glob. If any path is missing: remove it, find the correct path, or note in the objective.

### Source Verification

Always include `verification_requirements` to remind doc-writer:
1. Never assume file locations — use Glob
2. Never write code from memory — use Read
3. Never invent function names — use Grep
4. Always include line numbers
