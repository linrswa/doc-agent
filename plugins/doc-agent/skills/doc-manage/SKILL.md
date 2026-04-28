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
- When recording a "X was renamed/removed" reminder in `verification_requirements`, prefix it with `[delta]` so it can be cleaned up once absorbed into the target doc. See [verification_requirements entry classes](#verification_requirements-entry-classes).
- Before writing `dispatch.json`, validate the proposed content against `validate-dispatch.py` rules — particularly the `scope_in` cap of 6 items. If a change would exceed the cap, surface to the user and propose consolidation (merge ≥2 bullets into a higher-level category) or splitting the module — do not append past the cap and rely on the Write hook to catch it later.
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
5. **Handle stale_entry mismatches**: if response includes `config_mismatch` with `type: PROJECT_SPECIAL_CONSIDER` and `field: stale_entry`, surface each entry to the user (with `evidence` citation) and ask REMOVE / UPDATE / KEEP per entry. Apply confirmed edits to `project-special-consider.md`. This runs *after* handling the doc verdict — staleness does not block PASS. See [verification_requirements entry classes](#verification_requirements-entry-classes) for the analogous mechanism on the dispatch side.

---

## Reference

For dispatch format, review request format, task status mapping, config mismatch handling, and error handling details, see [references/formats.md](references/formats.md).

### verification_requirements entry classes

Two lifecycle classes, both stored as strings in the same array:

- **Durable** (no prefix): current-state facts re-derivable by `/gen-dispatch` from code — e.g., `"Line numbers must be accurate (within 5 lines tolerance)"`, `"ZMQ ports are GLOBAL (5560, 5561, 5562)"`. Rebuilt on regenerate; no explicit cleanup needed.
- **Delta** (`[delta]` prefix): refactor breadcrumb about a deleted/renamed symbol that writers must not regress to — e.g., `[delta] TriggerMaker mode enum REMOVED — interval-only, default 100ms`. NOT re-derivable from current code, so `/gen-dispatch` preserves these entries across regenerations. Removable once the target doc no longer references the old symbol; surface as a candidate for cleanup during UPDATE().

The `[delta]` marker is plain text — `validate-dispatch.py` does not enforce it. Both classes are equally authoritative during WRITE/REVIEW.

### Rules

- **Max 2 revisions** per module. 3rd REVISE > auto-block and ask user.
- **All documentation** in English.
- **Response format**: After each operation, report ACTION, DETAILS, NEXT_STEP, and use `TaskList` to show progress.
- **Project-specific considerations**: If `.doc-agents/project-special-consider.md` doesn't exist, create during first cycle with: tech stack, architecture patterns, key terminology, important directories, conventions.
- **Transient directives**: time-bound items (migration nudges, freeze windows) belong under a `## Transient` section in `project-special-consider.md`, each with an `(expires when: ...)` clause. doc-reviewer checks expiry conditions during normal review and reports met ones as `stale_entry` mismatches for cleanup. See [references/formats.md](references/formats.md#transient-section-convention-in-project-special-considermd).
