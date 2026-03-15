# dispatch.json Schema Reference

## JSON Structure

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

## Field Constraints

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

## Example Output

For a typical web application:

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
        "Line numbers must be accurate (within 5 lines tolerance)"
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
