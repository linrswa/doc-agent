---
name: doc-manage
description: "Orchestrate multi-agent documentation workflow — coordinates doc-writer and doc-reviewer agents to produce structured technical documentation in the docs/ directory with verified code citations. Use this skill for: /doc-manage, 'document the codebase', 'write technical docs', 'update documentation', 'review docs for accuracy', 'my docs are outdated', 'add documentation for this module', 'document this feature', or any request to create, update, review, or maintain structured project documentation. Even casual requests like 'help me with docs' or 'I need documentation' should trigger this skill. Do NOT use for: README edits, CLAUDE.md, inline code comments, JSDoc/docstrings, changelogs, or general text editing — those are standard tasks that don't need this workflow. If .doc-agents/dispatch.json exists, this skill manages the full pipeline; if not, it invokes gen-dispatch first."
---

# doc-manage

Coordinate documentation workflow by dispatching tasks to doc-writer and doc-reviewer agents. You do NOT write documents yourself — you orchestrate.

## Commands & Pipeline Selection

| Command | Pipeline |
|---------|----------|
| `/doc-manage` | UPDATE > WRITE > REVIEW (full workflow) |
| `/doc-manage {module}` | UPDATE > WRITE > REVIEW (single module) |
| `/doc-manage review {target}` | REVIEW only |
| `/doc-manage update` | UPDATE only (sync config) |
| `/doc-manage modify "{prompt}" {target}` | REVIEW > UPDATE > WRITE > REVIEW |

**Detection priority** — pick the first match:

1. User references a **specific existing doc** AND wants its content changed/updated to match code changes (e.g., "update docs/02-auth.md", "fix the docs for auth module", "docs are outdated for X") → **MODIFY**
2. `"review"` / `"check"` + specific doc path(s) to review → **REVIEW-ONLY**
3. Explicitly wants to **sync config only** (`/doc-manage update`, `"sync dispatch"`, `"update config"`) → **UPDATE-ONLY**
4. Everything else (including `"update docs"`, `"docs are outdated"`, `"document the codebase"`) → **DEFAULT**

Key distinction: "update the documentation" means the user wants docs regenerated (DEFAULT), NOT config sync (UPDATE-ONLY). UPDATE-ONLY is only for explicitly syncing `.doc-agents/` config files.

Proceed immediately when pipeline is clear. Only ask when truly ambiguous.

---

## Pipelines

### DEFAULT: `UPDATE > WRITE > REVIEW`

1. UPDATE()
2. Build execution plan from dependency graph, then create Task items
3. Execute: launch independent groups in parallel, dependency chains sequentially
   - Per module: WRITE(module) → REVIEW(document) → handle verdict
   - **PASS**: TaskUpdate completed | **REVISE**: re-WRITE (max 2 revisions) | **BLOCKED**: TaskUpdate blocked, ask user

#### Execution Planning

Parse `consistency_requirements` in `dispatch.json` to build dependency graph:
- If module A references module B → B before A
- Independent modules run in parallel; chains run sequentially

Example: api references auth, config references api:
```
parallel: [database] [utils] [auth > api > config]
```

**Task Tracking**: `TaskCreate` per module with `subject`, `activeForm`, `metadata.dispatch_id`, and `addBlockedBy` for chains.

### REVIEW-ONLY

1. Verify target(s) exist
2. Launch REVIEW() — parallel for multiple targets
3. PASS = done | REVISE = show fixes, ask next step | BLOCKED = show issues

### UPDATE-ONLY

1. UPDATE() → report findings

### MODIFY

1. REVIEW(target) — capture current issues
2. UPDATE()
3. WRITE(target, modification_prompt + review_findings)
4. REVIEW(updated_document) — handle verdict as DEFAULT

---

## Functions

### UPDATE()

Sync `.doc-agents/dispatch.json` and `.doc-agents/project-special-consider.md` with codebase state.

- **If config files missing**: suggest creating them
- Analyze codebase structure → compare with configs → auto-apply non-destructive updates
- For `dispatch.json` drift: re-run `/gen-dispatch`; for special-consider drift: edit directly
- Only stop and ask on CRITICAL mismatch or destructive update

### WRITE(module, [extra_context])

Requires `.doc-agents/dispatch.json` — if missing, call `/gen-dispatch` first.

1. Load dispatch template + `project-special-consider.md` + `block-list.json`
2. TaskUpdate: `in_progress`, phase `"writing"`
3. Dispatch via Agent tool (`subagent_type: "doc-agent:doc-writer"`) with dispatch fields + extra_context
4. Check response for config mismatch reports

### REVIEW(target_doc)

Requires target document to exist.

1. Load `project-special-consider.md` + `block-list.json`
2. TaskUpdate: phase `"reviewing"`
3. Dispatch via Agent tool (`subagent_type: "doc-agent:doc-reviewer"`) with review request
4. Check response for config mismatch reports

---

## Reference

For dispatch format, review request format, task status mapping, config mismatch handling, and error handling details, see [references/formats.md](references/formats.md).

### Rules

- **Max 2 revisions** per module. 3rd REVISE > auto-block and ask user.
- **All documentation** in English.
- **Response format**: After each operation, report ACTION, DETAILS, NEXT_STEP, and use `TaskList` to show progress.
- **Project-specific considerations**: If `.doc-agents/project-special-consider.md` doesn't exist, create during first cycle with: tech stack, architecture patterns, key terminology, important directories, conventions.
