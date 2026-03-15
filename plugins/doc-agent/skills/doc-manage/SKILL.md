---
name: doc-manage
description: "Manage documentation workflow for the codebase. Use when creating, updating, or organizing documentation including README files, API docs, code comments, CLAUDE.md files, and developer guides. This skill coordinates doc-writer and doc-reviewer agents. Triggers: /doc-manage, 'document the codebase', 'update docs', 'review documentation', 'modify docs', or any request to manage documentation workflow."
---

# doc-manage

Coordinate documentation workflow by dispatching tasks to doc-writer and doc-reviewer agents.

**IMPORTANT**: You do NOT write documents yourself. You coordinate and dispatch to doc-writer and doc-reviewer agents.

## Usage

| Command | Pipeline | Description |
|---------|----------|-------------|
| `/doc-manage` | UPDATE > WRITE > REVIEW | Full documentation workflow (default) |
| `/doc-manage {module}` | UPDATE > WRITE > REVIEW | Document a specific module |
| `/doc-manage review {target}` | REVIEW | Review existing document(s) only |
| `/doc-manage update` | UPDATE | Check and sync config files |
| `/doc-manage modify "{prompt}" {target}` | REVIEW > UPDATE > WRITE > REVIEW | Modify existing doc based on prompt |

## Pipeline Detection

| Priority | Keywords | Pipeline |
|----------|----------|----------|
| 1 | "modify", modification prompt for existing doc | **MODIFY** |
| 2 | "review", "check", `--review-only`, specific doc path to review | **REVIEW-ONLY** |
| 3 | "update", "sync" | **UPDATE-ONLY** |
| 4 | Default | **DEFAULT** |

Proceed immediately when pipeline is clear. Only ask when truly ambiguous.

---

## Pipelines

### DEFAULT: `UPDATE > WRITE > REVIEW`

1. UPDATE()
2. Initialize Task Tracking
3. Build execution plan (see Execution Planning)
4. Execute plan:
   - Launch independent groups in parallel
   - Within dependency chains, execute sequentially
   - Per module: WRITE(module) > REVIEW(document) > handle verdict
   - PASS: TaskUpdate completed | REVISE: increment revision_count, re-WRITE (max 2) | BLOCKED: TaskUpdate blocked, ask user
   - Unblock dependents after completion

#### Execution Planning

Build dependency graph from `consistency_requirements` in `dispatch.json`:

1. **Parse**: If module A's `consistency_requirements` references module B, then B before A
2. **Group**: Independent modules = parallel group; dependency chains = sequential
3. **Set task dependencies**: `TaskUpdate` with `addBlockedBy`

Example: modules auth, api, database, utils, config where api references auth and config references api:
```
parallel: [database] [utils] [auth > api > config]
```

**Task Tracking**: `TaskCreate` per module before execution with `subject`, `activeForm`, `metadata.dispatch_id`, and `addBlockedBy` for chains.

### REVIEW-ONLY: `REVIEW`

1. Verify target document(s) exist
2. Multiple targets: launch REVIEW() in parallel; single: REVIEW(target)
3. Report: PASS = done | REVISE = show fixes, ask next step | BLOCKED = show issues

### UPDATE-ONLY: `UPDATE`

1. UPDATE()
2. Report findings

### MODIFY: `REVIEW > UPDATE > WRITE > REVIEW`

1. REVIEW(target) — capture current state/issues
2. UPDATE()
3. Initialize Task Tracking
4. WRITE(target, modification_prompt + review_findings)
5. REVIEW(updated_document) — handle verdict as in DEFAULT

---

## Functions

### UPDATE()

Check if `.doc-agents/dispatch.json` and `.doc-agents/project-special-consider.md` are in sync with the codebase.

**If config files missing**: suggest creating them.

1. Analyze codebase structure (entry points, modules, tech stack)
2. Compare with `dispatch.json`: new/removed modules? changed paths in `repo_hints`?
3. Compare with `project-special-consider.md`: new frameworks? architecture changes?
4. Auto-apply updates (`dispatch.json`: re-run `/gen-dispatch`; special-consider: edit directly)
5. Show brief summary, continue to next pipeline step
6. Only stop and ask if CRITICAL mismatch or destructive update

### WRITE(module, [extra_context])

**Prerequisite**: `.doc-agents/dispatch.json` must exist. If missing, call `/gen-dispatch`.

1. Load dispatch template for module + `project-special-consider.md` + `.doc-agents/block-list.json`
2. TaskUpdate: status > `in_progress`, phase > `"writing"`
3. Dispatch to doc-writer via Agent tool (`subagent_type: "doc-agent:doc-writer"`) with dispatch fields + extra_context
4. Check response for config mismatch reports

### REVIEW(target_doc)

**Prerequisite**: Target document must exist.

1. Load `project-special-consider.md` + `.doc-agents/block-list.json`
2. TaskUpdate: phase > `"reviewing"` (if tracking active)
3. Dispatch to doc-reviewer via Agent tool (`subagent_type: "doc-agent:doc-reviewer"`) with review request
4. Check response for config mismatch reports

---

## Reference

For dispatch format, review request format, task status mapping, config mismatch handling, and error handling details, see [references/formats.md](references/formats.md).

### Rules

- **Max 2 revisions** per module. 3rd REVISE > auto-block and ask user.
- **All documentation** in English.
- **Response format**: After each operation, report ACTION, DETAILS, NEXT_STEP, and use `TaskList` to show progress.
- **Project-specific considerations**: If `.doc-agents/project-special-consider.md` doesn't exist, create during first cycle with: tech stack, architecture patterns, key terminology, important directories, conventions.
