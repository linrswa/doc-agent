---
name: gen-dispatch
description: "Generate dispatch templates for documentation workflow. Use when starting a documentation project or when project structure changes. Triggers: /gen-dispatch, 'generate dispatch', 'create dispatch templates', 'analyze project for documentation', or when .doc-agents/dispatch.json needs to be created or regenerated."
---

# gen-dispatch

Analyze the current project and generate `.doc-agents/dispatch.json` — a JSON bundle of dispatch entries for each module that should be documented. The `validate-dispatch.py` hook validates the JSON on every Write/Edit. The doc-manager agent uses these entries to dispatch tasks to doc-writer.

## Instructions

### Step 0: Load Block List

Read `.doc-agents/block-list.json` (if it exists). Files matching `patterns` array MUST be excluded from `repo_hints`.

### Step 1: Analyze Project Structure

Explore the codebase to identify:

1. **Entry points** — `main()` functions, `CMakeLists.txt` targets, `package.json` scripts
2. **Module boundaries** — directory structure, namespace/package organization, separation of concerns
3. **Communication layers** — API definitions (REST, GraphQL, gRPC), message protocols (protobuf, JSON schema), IPC (ZMQ, Redis, etc.)
4. **Configuration** — config file formats/locations, environment variables, settings schemas

### Step 2: Determine Documentation Modules

| Module Type | Purpose |
|-------------|---------|
| architecture | System overview, component relationships |
| protocols | Communication protocols, API specs |
| {component_name} | Individual component documentation |

### Step 3: Generate Dispatch Entries

For each module, generate a dispatch entry. See [references/schema.md](references/schema.md) for the full JSON schema, field constraints, and example output.

### Step 4: Create Task Items

After generating dispatch templates, create Task items for each module:

1. `TaskCreate` per module: `subject`: `"Document {module_name}"`, `description`: dispatch_id + target_doc + objective, `activeForm`: `"Documenting {module_name}"`, `metadata`: `{ "dispatch_id": "DOC-{module}-YYYYMMDD-{nn}" }`
2. `TaskUpdate` with `addBlockedBy` for dependency ordering — canonical source modules first, dependents blocked by their sources

### Step 5: Write Output

Write the dispatch bundle to `.doc-agents/dispatch.json`. Create `.doc-agents/` if needed.

Execution ordering is managed via Task tool dependencies (`blockedBy`/`blocks`), not in the dispatch file.

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
