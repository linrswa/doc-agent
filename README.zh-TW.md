# doc-agent

透過多代理自動管理文件——讓實作與你的心智模型保持連結。

## 為什麼需要 doc-agent？

在 AI 輔助開發的時代，程式碼的產出速度前所未有。但速度帶來了落差——實作不斷推進，你對它的理解卻未必跟上。如果沒有可靠的方式來驗證實際建構的內容，程式碼很容易在不知不覺中偏離你預期的架構。

doc-agent 正是為了填補這個落差而生。它讓 AI 代理自動產生**以實際原始碼為根據**的文件，每個描述都附上 `file:line` 引用。這不是為了寫文件而寫文件——而是一個驗證工具。透過閱讀產生的文件，你可以快速確認實作是否與你腦中的架構一致、及早發現架構偏移，並在快速演進的程式碼庫中維持信心。

## 功能特色

- **協調式工作流程**：`/doc-manage` 技能協調 doc-writer 和 doc-reviewer 代理，內建任務追蹤
- **上下文感知**：技能具有完整的對話上下文，能理解你剛才建構的內容
- **證據導向文件**：所有內容都需要 `file:line` 引用
- **動態門檻**：引用要求會隨模組大小動態調整
- **品質把關**：結構化審查，提供 PASS/REVISE/BLOCKED 判定結果
- **專案適應性**：透過設定檔進行專案特定的客製化

## 元件

### 技能

| 技能 | 用途 |
|------|------|
| `/doc-manage` | 協調工作流程、分派任務、追蹤進度 |
| `/gen-dispatch` | 為文件任務產生分派模板 |

### 代理

| 代理 | 角色 |
|------|------|
| `doc-agent:doc-writer` | 探索程式碼庫，寫附有引用的文件 |
| `doc-agent:doc-reviewer` | 審查文件品質，驗證引用 |

## 安裝

### 選項一：開發模式（暫時性）

```bash
claude --plugin-dir ./doc-agent
```

### 選項二：全域安裝（永久性）

#### 步驟一：複製儲存庫

```bash
git clone https://github.com/linrswa/doc-agent.git ~/doc-agent
```

#### 步驟二：建立本地市集（僅首次需要）

如果你還沒有本地市集：

```bash
mkdir -p ~/.claude/marketplaces/local/.claude-plugin
mkdir -p ~/.claude/marketplaces/local/plugins
```

建立 `~/.claude/marketplaces/local/.claude-plugin/marketplace.json`：

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

> 如果你已經有本地市集，只需將 `doc-agent` 項目加入現有的 `plugins` 列表中。

#### 步驟三：將外掛連結到市集

```bash
ln -s ~/doc-agent ~/.claude/marketplaces/local/plugins/doc-agent
```

#### 步驟四：新增市集並安裝

```bash
# 新增市集（僅首次需要）
claude plugin marketplace add ~/.claude/marketplaces/local

# 安裝外掛
claude plugin install doc-agent@local --scope user
```

#### 驗證安裝

```bash
claude plugin list
```

預期輸出：
```
  ❯ doc-agent@local
    Version: 0.1.0
    Scope: user
    Status: ✔ enabled
```

## 更新外掛

由於外掛是透過符號連結安裝的，只需拉最新變更並更新：

```bash
cd ~/doc-agent
git pull
claude plugin update doc-agent@local
```

然後重新啟動 Claude Code 工作階段以套用變更。

## 使用方式

### 快速開始

只需告訴 Claude 你建構了什麼：

```
I just added a new /api/users/{id}/profile endpoint
```

Claude 會主動使用 `/doc-manage` 來更新文件。

### 手動呼叫

```
/doc-manage
```

或指定特定目標：

```
/doc-manage authentication
```

### 產生分派模板

對於新專案，先產生分派模板：

```
/gen-dispatch
```

這會建立 `.doc-agents/dispatch-templates.md`，其中包含每個模組的 YAML 模板。

### 工作流程

1. `/doc-manage` 從 `.doc-agents/dispatch-templates.md` 載入模板
2. 根據模組依賴關係建立執行計畫——獨立模組平行執行，有依賴關係的模組依序執行
3. 對每個模組，將任務分派給 doc-writer 代理，指定具體範圍
4. doc-writer 探索程式碼，寫附有 `file:line` 引用的文件
5. `/doc-manage` 將文件送交 doc-reviewer 代理進行品質驗證
6. 重複修改直到通過（PASS）或達到最大修訂次數（2 次）；無法解決則上報使用者

## 工作目錄

所有工作檔案儲存在專案根目錄的 `.doc-agents/` 中：

```
.doc-agents/
├── dispatch-templates.md      # 由 /gen-dispatch 產生
└── project-special-consider.md # 專案特定考量
```

進度追蹤使用 Claude 內建的 Task 工具（`TaskCreate`、`TaskUpdate`、`TaskList`），而非檔案。

## 文件結構

產生的文件遵循標準化結構：

| 章節 | 必要 | 說明 |
|------|------|------|
| TL;DR | 是 | 3-5 個重點摘要 |
| 概述 | 是 | 模組目的與邊界 |
| 資料流程 | 有條件 | Mermaid 圖表（函式庫不適用） |
| 程式碼地圖 | 是 | 關鍵函式表格，附引用 |
| 疑難排解 | 有條件 | 問題情境（新模組不適用） |
| 擴充指南 | 是 | 如何擴充模組 |

### 可選章節

資料流程和疑難排解可標記為「不適用」，但需提供合理理由：

```markdown
## 資料流程

**不適用**：此模組為純工具函式庫，包含無狀態函式。
```

## 引用要求

引用會根據模組大小動態調整：

| 模組大小 | 檔案數 | 最少引用數 | 最少程式碼地圖 |
|----------|--------|-----------|---------------|
| 小 | 1-5 | 8 | 4 |
| 中 | 6-15 | 12-20 | 6-10 |
| 大 | 16+ | 20-30 | 10-15 |

### 支援的引用格式

| 格式 | 權重 | 範例 |
|------|------|------|
| 程式碼引用 | 1.0 | `src/auth/login.ts:42` |
| Proto 定義 | 1.0 | `api/user.proto:UserProfile` |
| 設定路徑 | 0.5 | `config/database.yml > connection.pool_size` |
| 章節錨點 | 0.5 | `docs/api.md#authentication` |
| 外部規範 | 0.5 | `[RFC-7231] url#section` |

## 設定

### 專案特定考量

建立 `.doc-agents/project-special-consider.md` 來為你的專案客製化：

```markdown
# 專案特定文件考量

## 技術堆疊
- 主要語言：Python、TypeScript
- 關鍵框架：FastAPI、React

## 術語表
| 術語 | 含義 |
|------|------|
| tenant | 多租戶架構中的組織或工作空間 |

## 重要路徑
- 進入點：src/main.py、src/index.ts
- 設定檔：config/

## 文件慣例
- 所有 API 端點須包含錯誤處理說明
- 在概述章節中記錄環境變數
```

## 外掛結構

```
doc-agent/
├── .claude-plugin/
│   └── plugin.json          # 外掛清單
├── agents/
│   ├── doc-writer.md        # 寫代理
│   └── doc-reviewer.md      # 審查代理
├── skills/
│   ├── doc-manage/
│   │   └── SKILL.md         # 文件協調技能
│   └── gen-dispatch/
│       └── SKILL.md         # 分派模板產生器
├── README.md
├── README.zh-TW.md
└── LICENSE
```

## 授權條款

MIT
