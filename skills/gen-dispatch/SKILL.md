---
name: gen-dispatch
description: "Generate dispatch templates for documentation workflow. Use when starting a documentation project or when project structure changes."
---

# gen-dispatch

Generate project-specific dispatch templates for the doc-manager agent.

## Usage

```
/gen-dispatch
```

Output files are written to `.doc-agents/`:
- `.doc-agents/dispatch-templates.md` - Dispatch templates for each module

## Description

This skill analyzes the current project structure and generates a `dispatch-templates.md` file containing YAML templates for each module that should be documented. The doc-manager agent uses these templates to dispatch documentation tasks to doc-writer.

## Instructions

When the user invokes `/gen-dispatch`, follow these steps:

### Step 0: Load Block List

Read `.doc-agents/block-list.json` (if it exists) and parse the `patterns` array. Files matching these patterns MUST be excluded from `repo_hints` in generated templates.

### Step 1: Analyze Project Structure

Explore the codebase to identify:

1. **Main executables/entry points** - Look for:
   - `main()` functions
   - `CMakeLists.txt` targets
   - `package.json` scripts
   - Entry point files in common locations

2. **Module boundaries** - Identify distinct modules by:
   - Directory structure (e.g., `src/module_name/`)
   - Namespace or package organization
   - Clear separation of concerns

3. **Communication layers** - Find:
   - API definitions (REST, GraphQL, gRPC)
   - Message protocols (protobuf, JSON schema)
   - Inter-process communication (ZMQ, Redis, etc.)

4. **Configuration files** - Locate:
   - Config file formats and locations
   - Environment variable usage
   - Settings schemas

### Step 2: Determine Documentation Modules

Based on analysis, decide which modules need documentation. Typical categories:

| Module Type | Purpose |
|-------------|---------|
| architecture | System overview, component relationships |
| protocols | Communication protocols, API specs |
| {component_name} | Individual component documentation |

### Step 3: Generate Dispatch Templates

For each identified module, generate a YAML template following this structure:

```yaml
dispatch_id: DOC-{module}-YYYYMMDD-01
module: {module_name}
target_doc: docs/{nn}-{module_name}.md

objective: >
  Single sentence describing the documentation goal

scope_in:
  - What to include (max 6 items)

scope_out:
  - What NOT to include

required_sections:
  - TL;DR
  - Overview
  - Data Flow
  - Code Map
  - Troubleshooting
  - Extension Guide

repo_hints:
  - Actual file paths to explore first
  - Key directories
  - Important entry points

canonical_sources:
  - docs/{protocol_doc}.md  # If applicable

consistency_requirements:
  - Cross-module consistency items
  - e.g., "Must be consistent with docs/00-protocols.md for API endpoint definitions"
  - Used by doc-manage for execution ordering (referenced modules must be documented first)

# CRITICAL: Source verification requirements
verification_requirements:
  - All file paths must be verified with Glob before referencing
  - All code snippets must be copied from Read output (not written from memory)
  - All function signatures must be verified with Grep
  - Line numbers must be accurate (±5 lines tolerance)
  - No "plausible-looking" code that wasn't actually read from source

acceptance_criteria:
  - Specific, verifiable criteria
  - Based on the module's characteristics
  - All code snippets verified against actual source files
  - No fictional code or assumed file locations
```

### Step 4: Create Task Items

After generating dispatch templates, create Task items for each module using Claude's built-in Task tools:

1. **Create a Task for each module** using `TaskCreate`:
   - `subject`: `"Document {module_name}"`
   - `description`: Include dispatch_id, target_doc path, and objective
   - `activeForm`: `"Documenting {module_name}"`
   - `metadata`: `{ "dispatch_id": "DOC-{module}-YYYYMMDD-{nn}" }`

2. **Set dependency ordering** using `TaskUpdate` with `addBlockedBy`:
   - Canonical source modules should have no blockers
   - Dependent modules should be blocked by their canonical sources
   - Example: if `protocols` must come before `backend`, set `backend` blocked by `protocols`

### Step 5: Output

Write the generated templates to `.doc-agents/dispatch-templates.md`.

**Note**: Create the `.doc-agents/` directory if it doesn't exist.

## Output Format

The generated `dispatch-templates.md` should include:

1. Header explaining the file's purpose
2. Each module's dispatch template in YAML code blocks
3. Usage instructions at the end

**Note**: Execution ordering is managed via Task tool dependencies (`blockedBy`/`blocks`), not in the templates file.

## Example

For a typical web application with backend and frontend:

```markdown
# Dispatch Templates

> Auto-generated dispatch templates for this project.
> Use with doc-manager agent.

## 1. Protocols

\`\`\`yaml
dispatch_id: DOC-protocols-YYYYMMDD-01
module: protocols
target_doc: docs/00-protocols.md
...
\`\`\`

## 2. Backend

\`\`\`yaml
dispatch_id: DOC-backend-YYYYMMDD-01
module: backend
target_doc: docs/01-backend.md
...
\`\`\`

## 3. Frontend

\`\`\`yaml
dispatch_id: DOC-frontend-YYYYMMDD-01
module: frontend
target_doc: docs/02-frontend.md
...
\`\`\`

---

## Usage

1. Copy the YAML for the module you want to document
2. Replace `YYYYMMDD` with today's date
3. Pass to doc-writer via doc-manager
```

## Template Validation

After generating templates, perform self-validation:

### Schema Validation Checklist

For each generated template, verify:

- [ ] `dispatch_id` matches pattern `DOC-{module}-YYYYMMDD-{nn}`
- [ ] `module` is non-empty string
- [ ] `target_doc` is valid path under `docs/`
- [ ] `objective` is single sentence (no line breaks)
- [ ] `scope_in` has 1-6 items
- [ ] `scope_out` has at least 1 item
- [ ] `repo_hints` contains only paths that exist
- [ ] `canonical_sources` paths exist (if specified)

### Block List Filtering

Before finalizing output, verify no `repo_hints` paths match block list patterns:

```
BLOCK_LIST_CHECK:

Template: DOC-{module}
  repo_hints:
    - src/module/: NOT BLOCKED
    - dist/bundle.js: BLOCKED (matches dist/**) <-- REMOVE THIS

  Result: PASS | FAIL (removed blocked entries)
```

### Path Existence Verification

Before finalizing output, verify all `repo_hints` paths:

```
VALIDATION_REPORT:

Template: DOC-{module}
  repo_hints:
    - src/module/: EXISTS
    - src/other/: EXISTS
    - src/typo/: NOT_FOUND  <-- FIX THIS

  Result: PASS | FAIL
```

**If any path does not exist, either:**
1. Remove it from repo_hints
2. Find the correct path
3. Mark as `# TODO: verify path` comment

### Output Validation Summary

At the end of `.doc-agents/dispatch-templates.md`, include:

```markdown
---

## Validation Summary

Generated: {local timestamp from: date +"%Y-%m-%dT%H:%M:%S%z"}
Modules: {count}
All paths verified: YES | NO

| Module | repo_hints Valid | canonical_sources Valid |
|--------|------------------|-------------------------|
| ...    | YES/NO           | YES/NO                  |
```

## Change Detection Metadata

Include metadata for change detection:

```markdown
---

## Generation Metadata

```yaml
generated_at: {local timestamp from: date +"%Y-%m-%dT%H:%M:%S%z"}
project_root: {absolute path}
structure_hash: {hash of CMakeLists + package.json + proto files}
entry_points_found:
  - {list of main files discovered}
modules_detected:
  - {list of module directories}
```

This allows doc-manager to detect when regeneration is needed.

## Notes

- The skill should adapt to different project types (C++, Python, Node.js, etc.)
- repo_hints should contain actual paths found during exploration
- canonical_sources should reflect the actual dependency order
- If a protocols/API spec file already exists, include it as canonical source
- **Always validate all paths before output**
- **Include generation metadata for change detection**

## Source Verification Emphasis

When generating templates, always include `verification_requirements` section to remind doc-writer:

1. **Never assume file locations** - Use Glob to find actual paths
2. **Never write code from memory** - Use Read to get actual code
3. **Never invent function names** - Use Grep to find actual definitions
4. **Always include line numbers** - Specific references, not just file names

This prevents documentation that "looks right" but doesn't match actual implementation.
