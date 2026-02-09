# 📝 doc-agent

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Claude Code Plugin](https://img.shields.io/badge/Claude_Code-Plugin-blue.svg)](https://claude.com/claude-code)

[繁體中文](README.zh-TW.md)

Automatically manage documentation with multiple agents — bridging the gap between implementation and your mental model.

## 🤔 Why doc-agent?

In the era of AI-assisted development, code is being written faster than ever. But speed creates a gap — the implementation moves forward while your understanding of it may not. Without a reliable way to verify what was actually built, it's easy for code to silently drift from your intended architecture.

doc-agent bridges this gap. It lets AI agents automatically generate documentation **grounded in actual source code**, with every claim backed by `file:line` citations. This isn't documentation for documentation's sake — it's a verification tool. By reading the generated docs, you can quickly check whether the implementation aligns with your mental model, catch architectural drift early, and maintain confidence in a rapidly evolving codebase.

## ✨ Features

- **Coordinated Workflow**: `/doc-manage` skill orchestrates doc-writer and doc-reviewer agents with built-in task tracking
- **Context-Aware**: The skill has full conversation context to understand what you just built
- **Evidence-Based Documentation**: All claims require `file:line` citations
- **Dynamic Thresholds**: Citation requirements scale with module size
- **Quality Gating**: Structured review with PASS/REVISE/BLOCKED verdicts
- **Project Adaptability**: Project-specific considerations via configuration

## 🧩 Components

### Skills

| Skill | Purpose |
|-------|---------|
| `/doc-manage` | Coordinates workflow, dispatches tasks, tracks progress |
| `/gen-dispatch` | Generates dispatch templates for documentation tasks |

### Agents

| Agent | Role |
|-------|------|
| `doc-agent:doc-writer` | Explores codebase, writes documentation with citations |
| `doc-agent:doc-reviewer` | Reviews documentation quality, verifies citations |

## 📦 Installation

### Option 1: Development Mode (Temporary)

```bash
claude --plugin-dir ./doc-agent
```

### Option 2: Global Installation (Permanent)

#### Step 1: Clone the repository

```bash
git clone https://github.com/linrswa/doc-agent.git ~/doc-agent
```

#### Step 2: Create a local marketplace (first time only)

If you don't have a local marketplace yet:

```bash
mkdir -p ~/.claude/marketplaces/local/.claude-plugin
mkdir -p ~/.claude/marketplaces/local/plugins
```

Create `~/.claude/marketplaces/local/.claude-plugin/marketplace.json`:

```json
{
  "name": "local",
  "description": "Local plugin marketplace for personal plugins",
  "owner": {
    "name": "your-name"
  },
  "plugins": [
    {
      "name": "doc-agent",
      "description": "Multi-agent documentation system with coordinated writing, reviewing, and management workflows",
      "source": "./plugins/doc-agent"
    }
  ]
}
```

> If you already have a local marketplace, just add the `doc-agent` entry to the existing `plugins` array.

#### Step 3: Link plugin to marketplace

```bash
ln -s ~/doc-agent ~/.claude/marketplaces/local/plugins/doc-agent
```

#### Step 4: Add marketplace and install

```bash
# Add marketplace (first time only)
claude plugin marketplace add ~/.claude/marketplaces/local

# Install plugin
claude plugin install doc-agent@local --scope user
```

#### Verify installation

```bash
claude plugin list
```

Expected output:
```
  ❯ doc-agent@local
    Version: 0.1.0
    Scope: user
    Status: ✔ enabled
```

## 🔄 Updating the Plugin

Since the plugin is symlinked, just pull the latest changes and update:

```bash
cd ~/doc-agent
git pull
claude plugin update doc-agent@local
```

Then restart your Claude Code session to apply changes.

## 🚀 Usage

### Quick Start

Just tell Claude what you built:

```
I just added a new /api/users/{id}/profile endpoint
```

Claude will proactively use `/doc-manage` to update documentation.

### Manual Invocation

```
/doc-manage
```

Or with a specific target:

```
/doc-manage authentication
```

### Generate Dispatch Templates

For new projects, first generate dispatch templates:

```
/gen-dispatch
```

This creates `.doc-agents/dispatch-templates.md` with YAML templates for each module.

### Workflow

1. `/doc-manage` loads templates from `.doc-agents/dispatch-templates.md`
2. Builds an execution plan based on module dependencies — independent modules run in parallel, dependent modules run sequentially
3. For each module, dispatches task to doc-writer agent with specific scope
4. doc-writer explores code, writes documentation with `file:line` citations
5. `/doc-manage` sends to doc-reviewer agent for quality verification
6. Iterate until PASS or max revisions (2) reached; escalate if blocked

## 📁 Working Directory

All working files are stored in `.doc-agents/` at the project root:

```
.doc-agents/
├── dispatch-templates.md      # Generated by /gen-dispatch
└── project-special-consider.md # Project-specific considerations
```

Progress tracking uses Claude's built-in Task tools (`TaskCreate`, `TaskUpdate`, `TaskList`) instead of a file.

## 📄 Documentation Structure

Generated documentation follows a standardized structure:

| Section | Required | Description |
|---------|----------|-------------|
| TL;DR | Yes | 3-5 key points summary |
| Overview | Yes | Module purpose and boundaries |
| Data Flow | Conditional | Mermaid diagram (N/A for libraries) |
| Code Map | Yes | Table of key functions with citations |
| Troubleshooting | Conditional | Problem scenarios (N/A for new modules) |
| Extension Guide | Yes | How to extend the module |

### Optional Sections

Data Flow and Troubleshooting can be marked "Not Applicable" with valid justification:

```markdown
## Data Flow

**Not Applicable**: This module is a pure utility library with stateless functions.
```

## 🔗 Citation Requirements

Citations scale dynamically based on module size:

| Module Size | Files | Min Citations | Min Code Map |
|-------------|-------|---------------|--------------|
| Small | 1-5 | 8 | 4 |
| Medium | 6-15 | 12-20 | 6-10 |
| Large | 16+ | 20-30 | 10-15 |

### Supported Citation Formats

| Format | Weight | Example |
|--------|--------|---------|
| Code reference | 1.0 | `src/auth/login.ts:42` |
| Proto definition | 1.0 | `api/user.proto:UserProfile` |
| Config path | 0.5 | `config/database.yml > connection.pool_size` |
| Section anchor | 0.5 | `docs/api.md#authentication` |
| External spec | 0.5 | `[RFC-7231] url#section` |

## ⚙️ Configuration

### Project-Specific Considerations

Create `.doc-agents/project-special-consider.md` to customize for your project:

```markdown
# Project-Specific Documentation Considerations

## Tech Stack
- Primary languages: Python, TypeScript
- Key frameworks: FastAPI, React

## Terminology
| Term | Meaning |
|------|---------|
| tenant | Organization or workspace in multi-tenant context |

## Important Paths
- Entry points: src/main.py, src/index.ts
- Configuration: config/

## Documentation Conventions
- Include error handling notes for all API endpoints
- Document environment variables in Overview section
```

## 🏗️ Plugin Structure

```
doc-agent/
├── .claude-plugin/
│   └── plugin.json          # Plugin manifest
├── agents/
│   ├── doc-writer.md        # Writer agent
│   └── doc-reviewer.md      # Reviewer agent
├── skills/
│   ├── doc-manage/
│   │   └── SKILL.md         # Documentation coordinator skill
│   └── gen-dispatch/
│       └── SKILL.md         # Dispatch template generator
├── README.md
└── LICENSE
```

## 📜 License

MIT
