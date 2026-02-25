# 📝 doc-agent

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Claude Code Plugin](https://img.shields.io/badge/Claude_Code-Plugin-blue.svg)](https://claude.com/claude-code)

[繁體中文](README.zh-TW.md)

Automatically manage documentation with multiple agents — bridging the gap between implementation and your mental model.

## 📢 Recent Updates

**v0.4.0** — Migrated dispatch format from YAML to JSON. Added `validate-dispatch.py` hook for schema validation on every Write/Edit.

**v0.3.0 ~ v0.3.2** — Migrated block list to JSON with `check-block-list.py` PreToolUse hook enforcement. Unified revision limits and citation validation standards.

**v0.2.0** — Extracted shared rules (`shared-rules.md`) and added block list support.

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

### Development Mode (Temporary)

```bash
claude --plugin-dir ./doc-agent
```

### Global Installation

**1. Clone the repository**

```bash
git clone https://github.com/linrswa/doc-agent.git ~/doc-agent
```

**2. Create a local marketplace** (first time only)

```bash
mkdir -p ~/.claude/marketplaces/local/.claude-plugin
mkdir -p ~/.claude/marketplaces/local/plugins
```

Create `~/.claude/marketplaces/local/.claude-plugin/marketplace.json`:

```json
{
  "name": "local",
  "description": "Local plugin marketplace for personal plugins",
  "owner": { "name": "your-name" },
  "plugins": [
    {
      "name": "doc-agent",
      "description": "Multi-agent documentation system",
      "source": "./plugins/doc-agent"
    }
  ]
}
```

> If you already have a local marketplace, just add the `doc-agent` entry to the existing `plugins` array.

**3. Link and install**

```bash
ln -s ~/doc-agent ~/.claude/marketplaces/local/plugins/doc-agent

# First time only
claude plugin marketplace add ~/.claude/marketplaces/local

# Install
claude plugin install doc-agent@local --scope user
```

**Updating**: Since the plugin is symlinked, run `cd ~/doc-agent && git pull && claude plugin update doc-agent@local`, then restart Claude Code.

## 🚀 Usage

Invoke `/doc-manage` first, then describe what to document in the follow-up prompt — this is the most reliable approach:

```
/doc-manage Document the new /api/users/{id}/profile endpoint
```

You can also target a specific module:

```
/doc-manage authentication
```

`/doc-manage` automatically checks whether dispatch templates exist and generates or updates them as needed — no manual `/gen-dispatch` required.

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
├── .claude-plugin/
│   └── plugin.json            # Plugin manifest
├── agents/
│   ├── shared-rules.md        # Shared rules (loaded at startup)
│   ├── doc-writer.md          # Writer agent definition
│   └── doc-reviewer.md        # Reviewer agent definition
├── hooks/
│   ├── hooks.json             # Hook definitions
│   ├── check-block-list.py    # Block list enforcement (Read)
│   └── validate-dispatch.py   # Dispatch schema validation (Write/Edit)
├── skills/
│   ├── doc-manage/
│   │   └── SKILL.md           # Documentation coordinator
│   └── gen-dispatch/
│       └── SKILL.md           # Dispatch template generator
└── .doc-agents/               # Per-project working directory
    ├── block-list.json        # Glob patterns to exclude
    ├── dispatch.json          # Module dispatch data
    └── project-special-consider.md
```

## 📜 License

MIT
