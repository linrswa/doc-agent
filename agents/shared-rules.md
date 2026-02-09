# Shared Rules for Documentation Agents

> **MANDATORY**: Both doc-writer and doc-reviewer agents MUST read and follow these rules before starting any task.

## Block List

Before referencing ANY file in documentation, check `.doc-agents/block-list.md` for excluded patterns.

### Rules

1. **Read** `.doc-agents/block-list.md` at the start of every task (skip if file doesn't exist)
2. Files matching any listed glob pattern MUST NOT appear in:
   - Code Map entries
   - Data Flow diagram nodes
   - Related Files Index
   - Code snippets or citations
   - `repo_hints` when generating dispatch templates
3. If a blocked file is the **only** evidence for critical information, note it in "Assumptions / To Be Confirmed" section without directly citing the file
4. Block list patterns use glob syntax (e.g., `dist/**`, `**/*.test.ts`, `node_modules/**`)

## Citation Formats

### Valid Citation Types

| Priority | Citation Type | Format | Use Case | Weight |
|----------|---------------|--------|----------|--------|
| 1 | Code reference | `file_path:line_number` | Source code, configs | 1.0 |
| 2 | Protocol definition | `file.proto:MessageName` | Protocol buffer definitions | 1.0 |
| 3 | Config path | `file_path > key.nested.path` | JSON/YAML configuration | 0.5 |
| 4 | Build file | `file_path:line_number` | CMakeLists.txt, package.json | 1.0 |
| 5 | Section anchor | `doc_path#section-name` | ADRs, design docs, READMEs | 0.5 |
| 6 | External spec | `[SPEC-ID] url#section` | RFCs, standards | 0.5 |

### Citation Examples

```
# Code reference (preferred, weight 1.0)
src/core/handler.cpp:78

# Proto definition (weight 1.0)
proto/frame.proto:FrameMetadata

# Config path (weight 0.5)
config/app_config.json > zmq.publisher.port

# Section anchor (weight 0.5)
docs/architecture/overview.md#data-flow

# External spec (weight 0.5)
[RFC-7231] https://tools.ietf.org/html/rfc7231#section-6.5.1
```

### Citation Validity Criteria

#### Code Reference (`file:line`)

- **VALID**: File exists, line number in bounds, content at that line relates to claimed functionality
- **INVALID**: File not found, line out of bounds, content unrelated (comment, blank line, wrong function)

#### Section Anchor (`doc#section`)

- **VALID**: Document exists, section heading exists (case-insensitive slug match), content relates to claim

#### Config Path (`file > key.path`)

- **VALID**: Config file exists, key path resolves to a value, value relates to claim

#### Proto Definition (`file.proto:Message`)

- **VALID**: Proto file exists, message/enum/service name exists in file, definition relates to claim

#### External Spec (`[SPEC-ID]`)

- **VALID**: Link is provided and accessible (or well-known standard), specific section/clause referenced

## Source Hierarchy

When conflicts exist between sources, follow this priority:

| Priority | Source | Wins Over |
|----------|--------|-----------|
| 1 | Running code behavior | Everything |
| 2 | Source code (`file:line`) | Docs, configs |
| 3 | Protocol definitions (.proto) | Higher-level docs |
| 4 | Canonical source docs | Module docs |
| 5 | Config files | Informal docs |
| 6 | READMEs, comments | Nothing |

## Dynamic Thresholds

Thresholds scale based on **module size** (number of source files in scope).

### Module Size Calculation

```
module_size = count of source files in scope (from dispatch repo_hints)
```

### Threshold Formulas

| Metric | Formula | Min | Max |
|--------|---------|-----|-----|
| Total `file:line` citations | `max(8, min(30, module_size * 2))` | 8 | 30 |
| Code Map entries | `max(4, min(15, module_size))` | 4 | 15 |
| Mermaid diagrams | 1 (if data flow applicable) | 0 | 2 |
| Troubleshooting scenarios | `max(2, min(5, module_size / 3))` | 2 | 5 |
| Extension guide examples | 2 | 2 | 4 |
| Invalid citations (spot check) | 0 | 0 | 0 |

### Module Size Categories

| Category | Files | Citation Min | Code Map Min | Troubleshooting Min |
|----------|-------|-------------|-------------|---------------------|
| Small | 1-5 | 8 | 4 | 2 |
| Medium | 6-15 | 12-20 | 6-12 | 2-3 |
| Large | 16+ | 20-30 | 12-15 | 4-5 |

### Per-Section Citation Guidelines

| Section | Small Module | Medium Module | Large Module |
|---------|-------------|--------------|-------------|
| TL;DR | 1-2 | 2 | 2-3 |
| Overview | 2 | 3 | 4 |
| Data Flow | 3 (or N/A) | 5 (or N/A) | 6+ (or N/A) |
| Code Map | 4 | 6-10 | 10-15 |
| Troubleshooting | 4 (or N/A) | 6-9 (or N/A) | 9+ (or N/A) |
| Extension Guide | 3 | 4 | 5 |

## Optional Sections (N/A Handling)

The following sections may be marked "Not Applicable" with valid justification:

| Section | Valid N/A Justifications |
|---------|-------------------------|
| Data Flow | Library/SDK with no runtime data flow; Pure utility functions; Schema-only module; Configuration module |
| Troubleshooting | New module with no known issues; Simple utility with obvious failure modes documented in Overview |

**Required N/A format:**

```markdown
## {Section Name}

**Not Applicable**: {Justification - e.g., "This module is a pure utility library with stateless functions."}
```

## Config Mismatch Reporting

While working with the codebase, if you discover that the actual implementation differs from what's described in `dispatch-templates.md` or `project-special-consider.md`, you MUST report it.

### Mismatch Types

| Mismatch Type | Example | Severity |
|---------------|---------|----------|
| Path changed | `repo_hints` references a deleted/moved directory | WARNING |
| New module | Major component not mentioned in dispatch | WARNING |
| Tech stack change | New framework/library in use | INFO |
| Architecture change | Different pattern than described | CRITICAL |
| Terminology change | Key terms renamed in codebase | WARNING |

### Mismatch Report Format

```yaml
config_mismatch:
  type: DISPATCH_TEMPLATE | PROJECT_SPECIAL_CONSIDER
  severity: INFO | WARNING | CRITICAL
  details:
    - field: {field_name}
      expected: {value in config}
      actual: {value found in codebase}
      suggestion: {recommended update}
```

**Do NOT silently work around mismatches.** Doc-manager needs this information to decide whether to update config files.

## Project-Specific Considerations

### Loading Project Context

If dispatch or review request references `project-special-consider.md`:

1. Read `.doc-agents/project-special-consider.md`
2. Apply tech stack, terminology, and conventions from that file
3. Use important paths as additional `repo_hints`
4. Follow documentation conventions specified

### Reporting New Discoveries

If you discover project-specific patterns not covered in the project context:

1. Note them in your report (KEY_FINDINGS for writer, summary for reviewer)
2. Examples:
   - Consistent naming patterns (e.g., all handlers end with `Handler`)
   - Important configuration files not documented
   - Cross-module dependencies
   - Protocol/port conventions
3. Doc-manager will decide whether to update `project-special-consider.md`

## Language Requirements

- **All documentation must be in English**
- Technical terms remain in English (do not translate)
- Review reports use English
