# 📝 doc-agent

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Claude Code Plugin](https://img.shields.io/badge/Claude_Code-Plugin-blue.svg)](https://claude.com/claude-code)

透過多代理自動管理文件——讓實作與你的心智模型保持連結。

## 📢 近期更新

**v0.4.4** — 優化 skill 描述與 pipeline 偵測邏輯。修正 MODIFY pipeline 歧義，消除 README/CLAUDE.md 的誤觸發。30 次 benchmark 測試達到 100% 準確率。

**v0.4.3** — 將 SKILL.md 中的參考細節抽取至獨立的 `references/` 文件。強化 `release.sh` 支援 release notes 與 dry-run。

**v0.4.2** — 移除中途確認步驟，讓 `/doc-manage` 自動跑完整個 pipeline 不中斷。

**v0.4.1** — 將外掛檔案移至 `plugins/doc-agent/` 子目錄，確保 marketplace 安裝乾淨。

**v0.4.0** — Dispatch 格式從 YAML 遷移至 JSON。新增 `validate-dispatch.py` hook，在每次 Write/Edit 時驗證 schema。

**v0.3.0 ~ v0.3.2** — 排除清單遷移至 JSON，新增 `check-block-list.py` PreToolUse hook 強制執行。統一修訂次數上限與引用驗證標準。

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

```bash
# 新增市集
claude plugin marketplace add linrswa/doc-agent

# 安裝外掛
claude plugin install doc-agent@doc-agent
```

## 🚀 使用方式

| 指令 | 功能 |
|------|------|
| `/doc-manage` | 完整流程：更新設定 → 撰寫 → 審查 |
| `/doc-manage {module}` | 為特定模組產生文件 |
| `/doc-manage review docs/01-api.md` | 審查現有文件的正確性 |
| `/doc-manage modify "更新 auth 相關內容" docs/02-auth.md` | 根據提示修改現有文件 |

`/doc-manage` 會自動檢查 dispatch 模板是否存在，並在需要時自動產生或更新——不需要手動執行 `/gen-dispatch`。

> **適用範圍：** doc-agent 產生的是 `docs/` 目錄下的結構化技術文件。它**不會**處理 README、CLAUDE.md、行內註解或 JSDoc——那些是一般編輯工作。

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
├── plugins/doc-agent/
│   ├── agents/
│   │   ├── shared-rules.md        # 共享規則（引用格式、閾值）
│   │   ├── doc-writer.md          # 撰寫代理（僅結構化文件）
│   │   └── doc-reviewer.md        # 審查代理（僅結構化文件）
│   ├── hooks/
│   │   ├── check-block-list.py    # 排除清單強制執行 (PreToolUse)
│   │   └── validate-dispatch.py   # Dispatch schema 驗證 (Write/Edit)
│   └── skills/
│       ├── doc-manage/SKILL.md    # 文件協調器
│       └── gen-dispatch/SKILL.md  # Dispatch 設定產生器
```

**專案層級檔案**（自動建立在 `.doc-agents/`）：
- `dispatch.json` — 模組 dispatch 模板
- `block-list.json` — 排除的 glob 模式
- `project-special-consider.md` — 專案背景資訊

## 📜 授權條款

MIT
