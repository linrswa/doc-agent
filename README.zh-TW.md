# 📝 doc-agent

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Claude Code Plugin](https://img.shields.io/badge/Claude_Code-Plugin-blue.svg)](https://claude.com/claude-code)

透過多代理自動管理文件——讓實作與你的心智模型保持連結。

## 📢 近期更新

**v0.4.0** — Dispatch 格式從 YAML 遷移至 JSON。新增 `validate-dispatch.py` hook，在每次 Write/Edit 時驗證 schema。

**v0.3.0 ~ v0.3.2** — 排除清單遷移至 JSON，新增 `check-block-list.py` PreToolUse hook 強制執行。統一修訂次數上限與引用驗證標準。

**v0.2.0** — 抽取共享規則（`shared-rules.md`），新增排除清單功能。

> **關於 hooks：** Hook 機制（`check-block-list.py`、`validate-dispatch.py`）目前僅經過命令列測試驗證，**尚未在實際文件產生流程中實戰測試過**。如遇到問題請回報。

## 🤔 為什麼需要 doc-agent？

在 AI 輔助開發的時代，程式碼的產出速度前所未有。但速度帶來了落差——實作不斷推進，你對它的理解卻未必跟上。

doc-agent 正是為了填補這個落差而生。它讓 AI 代理自動產生**以實際原始碼為根據**的文件，每個描述都附上 `file:line` 引用。透過閱讀產生的文件，你可以快速確認實作是否與你腦中的架構一致。

## 🔄 運作方式

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
|         +--[ dispatch ]----> doc-writer ----+                     |
|         |                    - explores code |                    |
|         |                    - writes docs   |                    |
|         |                    - adds file:line|                    |
|         |                      citations     |                    |
|         |<---[ draft ]----------------------+                     |
|         |                                                         |
|         +--[ review ]-----> doc-reviewer ---+                     |
|         |                   - checks quality |                    |
|         |                   - verifies refs   |                   |
|         |<---[ verdict ]--------------------+                     |
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

## 📦 安裝

### 開發模式（暫時性）

```bash
claude --plugin-dir ./doc-agent
```

### 全域安裝

**1. 複製儲存庫**

```bash
git clone https://github.com/linrswa/doc-agent.git ~/doc-agent
```

**2. 建立本地市集**（僅首次需要）

```bash
mkdir -p ~/.claude/marketplaces/local/.claude-plugin
mkdir -p ~/.claude/marketplaces/local/plugins
```

建立 `~/.claude/marketplaces/local/.claude-plugin/marketplace.json`：

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

> 如果你已經有本地市集，只需將 `doc-agent` 項目加入現有的 `plugins` 列表中。

**3. 連結並安裝**

```bash
ln -s ~/doc-agent ~/.claude/marketplaces/local/plugins/doc-agent

# 僅首次需要
claude plugin marketplace add ~/.claude/marketplaces/local

# 安裝
claude plugin install doc-agent@local --scope user
```

**更新**：由於外掛是透過符號連結安裝的，執行 `cd ~/doc-agent && git pull && claude plugin update doc-agent@local`，然後重新啟動 Claude Code。

## 🚀 使用方式

先呼叫 `/doc-manage`，再於後續提示中描述要記錄的內容——這是最穩定的做法：

```
/doc-manage Document the new /api/users/{id}/profile endpoint
```

也可以指定特定模組：

```
/doc-manage authentication
```

`/doc-manage` 會自動檢查 dispatch 模板是否存在，並在需要時自動產生或更新——不需要手動執行 `/gen-dispatch`。

## ⚙️ 設定

### 排除清單

建立 `.doc-agents/block-list.json` 來排除不需納入文件參考的檔案：

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

外掛層級的 `PreToolUse` hook 會強制執行此規則。預設已包含 `**/CLAUDE.md`。

### 專案特定考量

建立 `.doc-agents/project-special-consider.md` 來提供專案背景（技術堆疊、術語、慣例），代理在產生文件時會參考此檔案。

## 🏗️ 外掛結構

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

## 📜 授權條款

MIT
