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
- `.doc-agents/dispatch.json` - JSON dispatch bundle for all modules

## Description

This skill analyzes the current project structure and generates a `dispatch.json` file containing a JSON bundle with dispatch entries for each module that should be documented. The file is validated by a `PreToolUse` hook (`validate-dispatch.py`) on every Write/Edit. The doc-manager agent uses these entries to dispatch documentation tasks to doc-writer.

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

### Step 3: Generate Dispatch Entries

For each identified module, generate a dispatch entry in the JSON bundle.

#### JSON Schema

The output file (`.doc-agents/dispatch.json`) must conform to this structure:

```json
{
  "schema_version": "1.0.0",
  "meta": {
    "generated_at": "<local timestamp>",
    "generated_by": "gen-dispatch",
    "git_commit": "<short SHA or null>"
  },
  "dispatches": [
    {
      "dispatch_id": "DOC-{module}-YYYYMMDD-NN",
      "module": "{module_name}",
      "target_doc": "docs/{nn}-{module_name}.md",
      "objective": "Single sentence describing the documentation goal (min 10 chars)",
      "scope_in": ["What to include (max 6 items)"],
      "scope_out": ["What NOT to include"],
      "required_sections": ["TL;DR", "Overview", "Data Flow", "Code Map", "Troubleshooting", "Extension Guide"],
      "repo_hints": ["Actual file paths to explore first"],
      "canonical_sources": [],
      "consistency_requirements": [],
      "verification_requirements": ["All file paths must be verified with Glob before referencing"],
      "acceptance_criteria": ["Specific, verifiable criteria"]
    }
  ]
}
```

#### Field Constraints

| Field | Type | Constraint |
|-------|------|------------|
| `dispatch_id` | string | Pattern: `DOC-[a-z0-9_]+-YYYYMMDD-NN` |
| `module` | string | Pattern: `[a-z0-9][a-z0-9_-]*`; unique across dispatches |
| `target_doc` | string | Pattern: `docs/NN-name.md` |
| `objective` | string | Min 10 characters |
| `scope_in` | array | 1-6 non-empty strings |
| `scope_out` | array | >= 1 non-empty string |
| `required_sections` | array | Non-empty strings |
| `repo_hints` | array | Non-empty strings; paths that exist |
| `canonical_sources` | array | Non-empty strings (may be empty array) |
| `consistency_requirements` | array | Non-empty strings (may be empty array); used by doc-manage for execution ordering |
| `verification_requirements` | array | Non-empty strings |
| `acceptance_criteria` | array | Non-empty strings |

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

Write the generated dispatch bundle to `.doc-agents/dispatch.json`.

**Note**: Create the `.doc-agents/` directory if it doesn't exist. The `validate-dispatch.py` hook will automatically validate the JSON on Write.

**Note**: Execution ordering is managed via Task tool dependencies (`blockedBy`/`blocks`), not in the dispatch file.

## Output Format

The generated `dispatch.json` is a single JSON file. Example for a typical web application:

```json
{
  "schema_version": "1.0.0",
  "meta": {
    "generated_at": "2026-02-25T14:30:00+0800",
    "generated_by": "gen-dispatch",
    "git_commit": "abc1234"
  },
  "dispatches": [
    {
      "dispatch_id": "DOC-protocols-20260225-01",
      "module": "protocols",
      "target_doc": "docs/00-protocols.md",
      "objective": "Document API protocols, message formats, and communication patterns",
      "scope_in": ["REST API endpoints", "WebSocket events", "Message schemas"],
      "scope_out": ["Implementation details of individual handlers"],
      "required_sections": ["TL;DR", "Overview", "Data Flow", "Code Map", "Troubleshooting", "Extension Guide"],
      "repo_hints": ["src/api/", "proto/", "src/ws/"],
      "canonical_sources": [],
      "consistency_requirements": [],
      "verification_requirements": [
        "All file paths must be verified with Glob before referencing",
        "All code snippets must be copied from Read output (not written from memory)",
        "All function signatures must be verified with Grep",
        "Line numbers must be accurate (±5 lines tolerance)"
      ],
      "acceptance_criteria": [
        "All API endpoints documented with request/response formats",
        "All code snippets verified against actual source files"
      ]
    },
    {
      "dispatch_id": "DOC-backend-20260225-01",
      "module": "backend",
      "target_doc": "docs/01-backend.md",
      "objective": "Document backend service architecture, request handling, and data processing",
      "scope_in": ["Request lifecycle", "Middleware chain", "Database access", "Error handling"],
      "scope_out": ["Frontend components", "Deployment configuration"],
      "required_sections": ["TL;DR", "Overview", "Data Flow", "Code Map", "Troubleshooting", "Extension Guide"],
      "repo_hints": ["src/server/", "src/middleware/", "src/db/"],
      "canonical_sources": ["docs/00-protocols.md"],
      "consistency_requirements": ["Must be consistent with docs/00-protocols.md for API endpoint definitions"],
      "verification_requirements": [
        "All file paths must be verified with Glob before referencing",
        "All code snippets must be copied from Read output (not written from memory)"
      ],
      "acceptance_criteria": [
        "Request lifecycle fully traced with file:line citations",
        "No fictional code or assumed file locations"
      ]
    }
  ]
}
```

## Pre-Output Validation

The `validate-dispatch.py` hook automatically validates schema on Write. Before writing, perform these additional prompt-level checks:

### Block List Filtering

Verify no `repo_hints` paths match block list patterns:

```
BLOCK_LIST_CHECK:

Dispatch: DOC-{module}
  repo_hints:
    - src/module/: NOT BLOCKED
    - dist/bundle.js: BLOCKED (matches dist/**) <-- REMOVE THIS

  Result: PASS | FAIL (removed blocked entries)
```

### Path Existence Verification

Verify all `repo_hints` paths exist:

```
VALIDATION_REPORT:

Dispatch: DOC-{module}
  repo_hints:
    - src/module/: EXISTS
    - src/other/: EXISTS
    - src/typo/: NOT_FOUND  <-- FIX THIS

  Result: PASS | FAIL
```

**If any path does not exist, either:**
1. Remove it from repo_hints
2. Find the correct path
3. Add a note in the objective

## Notes

- The skill should adapt to different project types (C++, Python, Node.js, etc.)
- repo_hints should contain actual paths found during exploration
- canonical_sources should reflect the actual dependency order
- If a protocols/API spec file already exists, include it as canonical source
- **Always validate all paths before output**
- **Metadata lives in the JSON `meta` field** (generated_at, generated_by, git_commit)

## Source Verification Emphasis

When generating dispatch entries, always include `verification_requirements` to remind doc-writer:

1. **Never assume file locations** - Use Glob to find actual paths
2. **Never write code from memory** - Use Read to get actual code
3. **Never invent function names** - Use Grep to find actual definitions
4. **Always include line numbers** - Specific references, not just file names

This prevents documentation that "looks right" but doesn't match actual implementation.
