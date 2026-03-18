# 📝 doc-agent

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Claude Code Plugin](https://img.shields.io/badge/Claude_Code-Plugin-blue.svg)](https://claude.com/claude-code)

[繁體中文](README.zh-TW.md)

Automatically manage documentation with multiple agents — bridging the gap between implementation and your mental model.

## 📢 Recent Updates

**v0.4.4** — Optimized skill descriptions and pipeline detection. Fixed MODIFY pipeline ambiguity, eliminated false triggers on README/CLAUDE.md tasks. Benchmarked at 100% accuracy across 30 runs.

**v0.4.0** — Migrated dispatch format from YAML to JSON. Added `validate-dispatch.py` hook for schema validation on every Write/Edit.

**v0.3.0 ~ v0.3.2** — Migrated block list to JSON with `check-block-list.py` PreToolUse hook enforcement. Unified revision limits and citation validation standards.

> **Note on hooks:** The hook mechanism (`check-block-list.py`, `validate-dispatch.py`) has only been verified via command-line testing — it has **not yet been battle-tested in real documentation runs**. Please report any issues you encounter.

## 🤔 Why doc-agent?

In the era of AI-assisted development, code is written faster than ever. But speed creates a gap — the implementation moves forward while your understanding may not.

doc-agent bridges this gap. It generates documentation **grounded in actual source code**, with every claim backed by `file:line` citations. By reading the generated docs, you can quickly verify whether the implementation matches your mental model.

## 🔄 How It Works

```
+-------------------------------------------------------------------+
|                        Claude Code Session                        |
+-------------------------------------------------------------------+
|                                                                   |
|  User: /doc-manage Document the new auth module                   |
|         |                                                         |
|         |  auto-generates/updates dispatch.json                   |
|         |  via /gen-dispatch if needed                            |
|         |                                                         |
|         +--[ dispatch ]----> doc-writer -----+                    |
|         |                    - explores code |                    |
|         |                    - writes docs   |                    |
|         |                    - adds file:line|                    |
|         |                      citations     |                    |
|         |<---[ draft ]-----------------------+                    |
|         |                                                         |
|         +--[ review ]-----> doc-reviewer ----+                    |
|         |                   - checks quality |                    |
|         |                   - verifies refs  |                    |
|         |<---[ verdict ]---------------------+                    |
|         |                                                         |
|         +---> PASS -----> Done                                    |
|         +---> REVISE ---> retry (max 2)                           |
|         +---> BLOCKED --> escalate to user                        |
|                                                                   |
|  * Both agents load shared-rules.md at startup                    |
|  * Block-list hook prevents reading excluded files                |
|  * Dispatch hook validates dispatch.json on write                 |
+-------------------------------------------------------------------+
```

## 📦 Installation

```bash
# Add the marketplace
claude plugin marketplace add linrswa/doc-agent

# Install the plugin
claude plugin install doc-agent@doc-agent
```

## 🚀 Usage

| Command | What it does |
|---------|-------------|
| `/doc-manage` | Full workflow: update config → write → review |
| `/doc-manage {module}` | Document a specific module |
| `/doc-manage review docs/01-api.md` | Review existing docs for accuracy |
| `/doc-manage modify "update for new auth" docs/02-auth.md` | Modify existing doc based on prompt |

`/doc-manage` automatically checks whether dispatch templates exist and generates or updates them as needed — no manual `/gen-dispatch` required.

> **Scope:** doc-agent produces structured technical documentation in the `docs/` directory. It does **not** handle README, CLAUDE.md, inline comments, or JSDoc — those are standard editing tasks.

## ⚙️ Configuration

### Block List

Create `.doc-agents/block-list.json` to exclude files from documentation references:

```json
{
  "description": "Files matching patterns below are excluded from all documentation references",
  "patterns": [
    "**/CLAUDE.md",
    "node_modules/**",
    "dist/**"
  ]
}
```

A `PreToolUse` hook enforces this at the plugin level. `**/CLAUDE.md` is included by default.

### Project-Specific Considerations

Create `.doc-agents/project-special-consider.md` to provide project context (tech stack, terminology, conventions) that agents will reference during documentation.

## 🏗️ Plugin Structure

```
doc-agent/
├── plugins/doc-agent/
│   ├── agents/
│   │   ├── shared-rules.md        # Shared rules (citation, thresholds)
│   │   ├── doc-writer.md          # Writer agent (structured docs only)
│   │   └── doc-reviewer.md        # Reviewer agent (structured docs only)
│   ├── hooks/
│   │   ├── check-block-list.py    # Block list enforcement (PreToolUse)
│   │   └── validate-dispatch.py   # Dispatch schema validation (Write/Edit)
│   └── skills/
│       ├── doc-manage/SKILL.md    # Documentation coordinator
│       └── gen-dispatch/SKILL.md  # Dispatch config generator
```

**Per-project files** (created automatically in `.doc-agents/`):
- `dispatch.json` — Module dispatch templates
- `block-list.json` — Glob patterns to exclude
- `project-special-consider.md` — Project context

## 📜 License

MIT
