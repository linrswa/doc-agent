# Dispatch & Review Formats Reference

## Dispatch Format (to doc-writer)

Sourced from `.doc-agents/dispatch.json`. Each entry in the `dispatches` array contains these fields. Format them into the prompt when dispatching via the Agent tool:

| Field | Description |
|-------|-------------|
| `dispatch_id` | Unique ID (pattern: `DOC-[a-z0-9_]+-YYYYMMDD-NN`) |
| `module` | Module name |
| `target_doc` | Output file path (pattern: `docs/NN-name.md`) |
| `objective` | Single sentence goal (min 10 chars) |
| `scope_in` | What to include (1-6 items) |
| `scope_out` | What NOT to include |
| `required_sections` | Sections the doc must contain |
| `repo_hints` | Directories/files to explore first |
| `canonical_sources` | Authoritative source documents |
| `consistency_requirements` | Cross-document consistency items |
| `verification_requirements` | Source verification rules |
| `acceptance_criteria` | Criteria for completion |

Additionally include `block_list` patterns from `.doc-agents/block-list.json` (if exists) in the dispatch context.

## Review Request Format (to doc-reviewer)

```yaml
review_request:
  dispatch_id: {original dispatch ID or REVIEW-{filename}-{yyyymmdd}-{nn}}
  target_doc: {target document path}
  canonical_sources:
    - {list of authoritative sources}
  block_list:
    - Glob patterns from .doc-agents/block-list.json (if exists)
```

## Task Status Mapping

| State | `status` | `metadata.phase` |
|-------|----------|-------------------|
| TODO | `pending` | -- |
| Writing | `in_progress` | `"writing"` |
| Reviewing | `in_progress` | `"reviewing"` |
| Revision | `in_progress` | `"revision"` |
| Done | `completed` | -- |
| Blocked | `in_progress` | `"blocked"` |

**Metadata fields**: `dispatch_id`, `revision_count` (max 2 then auto-block), `reason` (when blocked).

## Config Mismatch Handling

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

## Error Handling

| Situation | Action |
|-----------|--------|
| Target doc missing | Report, suggest similar files, ask user |
| doc-writer returns PARTIAL | TaskUpdate with note, create follow-up or accept |
| Invalid paths in `repo_hints` | Use Glob to find correct paths |
