---
name: doc-manage
description: "Manage documentation workflow for the codebase. Use when creating, updating, or organizing documentation including README files, API docs, code comments, CLAUDE.md files, and developer guides. This skill coordinates doc-writer and doc-reviewer agents."
---

# doc-manage

Coordinate documentation workflow by dispatching tasks to doc-writer and doc-reviewer agents.

## Usage

```
/doc-manage [target] [options]
```

| Command | Pipeline | Description |
|---------|----------|-------------|
| `/doc-manage` | `UPDATE → WRITE → REVIEW` | Full documentation workflow (default) |
| `/doc-manage {module}` | `UPDATE → WRITE → REVIEW` | Document a specific module |
| `/doc-manage review {target}` | `REVIEW` | Review existing document(s) only |
| `/doc-manage update` | `UPDATE` | Check and sync config files |
| `/doc-manage modify "{prompt}" {target}` | `REVIEW → UPDATE → WRITE → REVIEW` | Modify existing doc based on prompt |

**IMPORTANT**: You do NOT write documents yourself. You coordinate and dispatch to doc-writer and doc-reviewer agents.

## Pipeline Detection

**CRITICAL**: First determine which pipeline the user needs.

| Priority | Keywords | Pipeline |
|----------|----------|----------|
| 1 | "modify", "修改", modification prompt for existing doc | **MODIFY** |
| 2 | "review", "check", "審查", "檢查", `--review-only`, specific doc path to review | **REVIEW-ONLY** |
| 3 | "update", "更新", "sync", "同步" | **UPDATE-ONLY** |
| 4 | Default (no special keywords) | **DEFAULT** |

Before starting, confirm scope with user based on conversation context. If unclear, ask which pipeline they want.

---

## Pipelines

### DEFAULT Pipeline: `UPDATE → WRITE → REVIEW`

```
1. UPDATE()
2. Initialize Task Tracking
3. Build execution plan (see Execution Planning below)
4. Execute plan:
   - Launch all independent groups in parallel
   - Within each dependency chain, execute sequentially
   - For each module (parallel or sequential as planned):
     a. WRITE(module) → document
     b. REVIEW(document) → verdict
     c. Handle verdict:
        - PASS    → TaskUpdate: completed
        - REVISE  → increment revision_count, go to (a), max 2
        - BLOCKED → TaskUpdate: blocked, ask user
     d. If module has dependents → unblock next module in chain
```

#### Execution Planning

Build a dependency graph from each module's `consistency_requirements` in `dispatch-templates.md`:

1. **Parse**: If module A's `consistency_requirements` references module B → B must complete before A (B → A)
2. **Group**:
   - **Independent** (no cross-references) → parallel group
   - **Dependency chain** → sequential, ordered by dependency direction
3. **Set task dependencies**: `TaskUpdate` with `addBlockedBy`

**Example**:
```
Modules: auth, api, database, utils, config

consistency_requirements:
  api → references auth       (auth before api)
  config → references api     (api before config)

Execution plan:
  parallel:  [database] [utils] [auth → api → config]
```

**Task Tracking**: `TaskCreate` for each module before execution:
- `subject`: `"Document {module_name}"`, `activeForm`: `"Documenting {module_name}"`
- `metadata`: `{ "dispatch_id": "DOC-{module}-YYYYMMDD-{nn}" }`
- Use `addBlockedBy` for dependency chains

### REVIEW-ONLY Pipeline: `REVIEW`

```
1. Verify target document(s) exist
2. If multiple targets → launch REVIEW() for each in parallel
   If single target  → REVIEW(target)
3. Report to user:
   - PASS    → Done
   - REVISE  → Show required fixes, ask user next step
   - BLOCKED → Show blocking issues
```

### UPDATE-ONLY Pipeline: `UPDATE`

```
1. UPDATE()
2. Report findings to user
```

### MODIFY Pipeline: `REVIEW → UPDATE → WRITE → REVIEW`

```
1. REVIEW(target) → capture current state and issues
2. UPDATE()
3. Initialize Task Tracking
4. WRITE(target, modification_prompt + review_findings) → updated document
5. REVIEW(updated_document) → verdict
6. Handle verdict (same as DEFAULT step 4c)
```

---

## Functions

### UPDATE()

Check if `.doc-agents/dispatch-templates.md` and `.doc-agents/project-special-consider.md` are in sync with the current codebase.

**Prerequisites**: `.doc-agents/` directory should exist. If config files are missing, suggest creating them.

**Steps**:
1. Analyze current codebase structure (entry points, modules, directories, tech stack)
2. Compare with existing `dispatch-templates.md`:
   - New modules not in templates?
   - Removed modules still in templates?
   - Changed paths in `repo_hints`?
3. Compare with existing `project-special-consider.md`:
   - New frameworks/libraries added?
   - Architecture patterns changed?
4. Report findings to user as a checklist
5. If user confirms → `dispatch-templates.md`: re-run `/gen-dispatch`; `project-special-consider.md`: edit directly

**Output**: Updated config files (or no changes needed).

### WRITE(module, [extra_context])

Dispatch documentation task to doc-writer agent.

**Prerequisites**: `.doc-agents/dispatch-templates.md` **must exist**. If missing, call `/gen-dispatch`. Halt if fails.

**Steps**:
1. Load dispatch template for target module + `project-special-consider.md` if exists
2. Load `.doc-agents/block-list.json` (if exists) and include block list patterns in the dispatch context
3. TaskUpdate: status → `in_progress`, phase → `"writing"`
4. Dispatch to doc-writer via Task tool (`subagent_type: "doc-agent:doc-writer"`) with dispatch YAML + `extra_context` if provided
5. Check response for config mismatch reports (see Reference)

**Output**: Written/updated documentation file.

### REVIEW(target_doc)

Pass document to doc-reviewer agent for review.

**Prerequisites**: Target document must exist.

**Steps**:
1. Load `project-special-consider.md` if exists
2. Load `.doc-agents/block-list.json` (if exists) and include block list patterns in the review context
3. TaskUpdate: phase → `"reviewing"` (if task tracking is active)
4. Dispatch to doc-reviewer via Task tool (`subagent_type: "doc-agent:doc-reviewer"`) with review request YAML
5. Check response for config mismatch reports (see Reference)

**Output**: Verdict (`PASS` / `REVISE` / `BLOCKED`) with details.

---

## Reference

### Dispatch Format (to doc-writer)

```yaml
dispatch_id: DOC-{module}-{yyyymmdd}-{nn}
module: {module_name}
target_doc: {target_path}

objective: >
  Single sentence describing the deliverable goal

scope_in:
  - Explicitly included aspects (max 6 items)

scope_out:
  - Explicitly excluded aspects

required_sections:
  - Overview
  - Data Flow
  - Code Map
  - Troubleshooting
  - Extension Guide

repo_hints:
  - Directories/files/keywords to explore first

canonical_sources:
  - {path to authoritative source documents}

consistency_requirements:
  - Items that must be consistent with other documents

block_list:
  - Glob patterns from .doc-agents/block-list.json (if exists)

acceptance_criteria:
  - Acceptance criteria list
```

### Review Request Format (to doc-reviewer)

```yaml
review_request:
  dispatch_id: {original dispatch ID or REVIEW-{filename}-{yyyymmdd}-{nn}}
  target_doc: {target document path}
  canonical_sources:
    - {list of authoritative sources}
  block_list:
    - Glob patterns from .doc-agents/block-list.json (if exists)
```

### Task Status Mapping

| State | `status` | `metadata.phase` |
|-------|----------|-------------------|
| TODO | `pending` | -- |
| Writing | `in_progress` | `"writing"` |
| Reviewing | `in_progress` | `"reviewing"` |
| Revision | `in_progress` | `"revision"` |
| Done | `completed` | -- |
| Blocked | `in_progress` | `"blocked"` |

**Metadata fields**: `dispatch_id`, `revision_count` (max 2 → auto-block), `reason` (when blocked).

### Config Mismatch Handling

Agents may report mismatches between config files and actual codebase:

```yaml
config_mismatch:
  type: {DISPATCH_TEMPLATE | PROJECT_SPECIAL_CONSIDER}
  severity: {INFO | WARNING | CRITICAL}
  details:
    - field: {field_name}
      expected: {value in config}
      actual: {value found in codebase}
      suggestion: {recommended update}
```

| Severity | Action |
|----------|--------|
| INFO | Log, report at end |
| WARNING | Pause, ask user |
| CRITICAL | Stop, get user decision |

### Error Handling

| Situation | Action |
|-----------|--------|
| Target doc missing | Report, suggest similar files, ask user |
| doc-writer returns PARTIAL | TaskUpdate with note, create follow-up or accept |
| Invalid paths in `repo_hints` | Use Glob to find correct paths |

### Rules

- **Max 2 revisions** per module. Revision 3 → auto-block, ask user.
- **All documentation** must be in English.
- **Response format**: After each operation, report ACTION, DETAILS, NEXT_STEP, and use `TaskList` to show progress.
- **Project-specific considerations**: If `.doc-agents/project-special-consider.md` doesn't exist, create during first cycle with: tech stack, architecture patterns, key terminology, important directories, conventions.
