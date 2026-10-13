---
title: SessionStart hooks for session-preferences and control-return
date: 2026-10-12
status: draft
---

# SessionStart hooks for `session-preferences` and `control-return`

## 1. Goal

讓 `session-preferences` 與 `control-return` 在 Claude Code 和 Codex 的每個 session 自動生效，不用每次手動打 `/session-preferences`、`/control-return`。

## 2. Confirmed decisions

- 兩個 skill 都改成常駐。hook 注入規則全文；skill 保留給 session 中手動補套用，以及 `session-preferences` 的 `add-rule`／`add-deai`。
- 各 runtime 讀自己的安裝目錄：Claude Code 讀 `~/.claude/skills`（symlink 到 `agent-skills-production` worktree），Codex 讀 `~/.codex/skills`（由 skill-sync 鏡像）。
- 環境變數 `AGENT_SESSION_PREFS=off` 時，兩支腳本都不注入。一個變數同時關兩個，不做個別開關。
- matcher 為 `startup|clear|compact`，不含 `resume`、`fork`。前提是接續 session 時舊注入內容仍保留，見第 7 節實驗。
- 每個 skill 自帶 `scripts/session_start_hook.py`，每個 runtime 各掛兩個 hook。
- 實作語言為 Python，輸出 JSON（方向 A）。不採 Bash + jq（抽 markdown 區塊脆弱）或純文字 stdout（Codex 遇到像 JSON 但解析失敗的輸出會讓 hook 失敗，也沒有 `systemMessage` 可警告）。
- 注入內容開頭註明：跟 output style、`CLAUDE.md`、`AGENTS.md` 衝突時，以那些為準。
- hook 模式不輸出「已啟用…」那句。

與 `/lesson` 的差異：lesson 設計選擇讓所有 agent 用指令呼叫同一支腳本、不依賴 hook（見 `2026-09-30-lesson-capture-design.md` 第 2 節）。本設計只涵蓋 Claude Code 與 Codex，兩者都有 SessionStart hook，所以直接使用。

## 3. Verified facts

- 兩個 skill 都設 `disable-model-invocation: true`（Codex：`allow_implicit_invocation: false`）。hook 無法讓模型呼叫 skill，只能注入規則內文。
- Codex 0.162.1 支援 `SessionStart`，source 值為 `startup|resume|clear|compact|fork`；輸出 schema 有 `hookSpecificOutput.additionalContext` 與 `systemMessage`。來源：`openai/codex` 的 `codex-rs/hooks/src/events/session_start.rs`、`codex-rs/hooks/schema/generated/session-start.command.output.schema.json`。
- Codex 的 user hook 沒有 `trusted_hash` 時為 Untrusted，需要使用者核准。來源：`codex-rs/hooks/src/engine/discovery.rs`。
- 常駐內容大小：`INDEX.md` 加三個常駐模組約 3.6 KB，control-return 規則約 0.5 KB。
- 2026-10-12 時 `~/.codex/skills/session-preferences` 落後：缺 `explanation-depth.md`，`INDEX.md` 不同。

NOT VERIFIED：Codex `additional_context_limit` 的預設值；resume 時舊注入內容是否保留（兩個 runtime 都要確認）。

## 4. Architecture

```
session-preferences/
├── SKILL.md
├── references/INDEX.md, deai-voice.md, ...
└── scripts/session_start_hook.py   ← 新增
control-return/
├── SKILL.md
└── scripts/session_start_hook.py   ← 新增
```

腳本以 `Path(__file__).resolve().parent.parent` 找 skill 目錄，不寫死路徑。同一支腳本在 `~/.claude/skills` 讀那份，同步到 `~/.codex/skills` 就讀 Codex 那份。

### Data flow

```
hook 啟動（stdin 為 hook 輸入，內容不影響輸出）
  │
  ├─ AGENT_SESSION_PREFS=off ? ──是──> 不輸出，exit 0
  │
  ├─ session-preferences：
  │    讀 references/INDEX.md → 解析表格 File 欄 → 依序讀各模組
  │    附「延後讀取參考檔」對照：references/ 內不在 INDEX 的 .md → 絕對路徑
  │
  ├─ control-return：
  │    讀 SKILL.md → 抽 "## Rule" 底下第一個 ```text 區塊
  │
  └─ stdout：
       {"hookSpecificOutput": {"hookEventName": "SessionStart",
                               "additionalContext": "<開頭說明 + 規則全文>"}}
```

模組原文一字不改，只在前後加說明。之後用 `add-rule` 改模組，下個 session 就生效。

session-preferences 注入內容的開頭：

```
[session-preferences — auto-applied by SessionStart hook]
Apply the following modules for this session. Do not announce activation.
If they conflict with the active output style, CLAUDE.md, or AGENTS.md, those take precedence.
```

control-return 用同樣格式的開頭，接規則全文。

## 5. Configuration and skill changes

### Claude Code：`~/.claude/settings.json`

用 `update-config` 在既有 `SessionStart` 陣列新增一組，`cc-status` 不動：

```json
{
  "matcher": "startup|clear|compact",
  "hooks": [
    { "type": "command", "command": "python3 /Users/tom_wang/.claude/skills/session-preferences/scripts/session_start_hook.py", "timeout": 5 },
    { "type": "command", "command": "python3 /Users/tom_wang/.claude/skills/control-return/scripts/session_start_hook.py", "timeout": 5 }
  ]
}
```

### Codex：`~/.codex/hooks.json`

新增 `SessionStart`，格式照現有已核准的 `PreToolUse` entry，路徑改為 `/Users/tom_wang/.codex/skills/...`。上線順序：

1. repo 改動合併到 production（`~/.claude/skills` 才會有新腳本）。
2. 先給使用者看 skill-sync 預覽（含刪除數），確認後才同步到 `~/.codex/skills`。
3. 寫入 `hooks.json`，由使用者在 Codex 核准新 hook。
4. 確認現有 `PreToolUse` 的 trusted 狀態沒有變。

### SKILL.md 與周邊檔案

`disable-model-invocation: true` 保留。

| 位置 | 現在 | 改成 |
|---|---|---|
| 兩份 description | 「…Never enable automatically.」 | 每個 session 由 SessionStart hook 自動套用；手動指令用於 session 中補套用（session-preferences 另有 add-rule） |
| session-preferences Activation | 「Do not apply rules … in a new session」 | hook 已在新 session 套用；手動指令是 hook 沒跑時的補救 |
| control-return | 「There is no off command」 | 補充：開 session 前設 `AGENT_SESSION_PREFS=off` 可不載入；session 中要停，照原規則叫停就停 |
| 兩份新增 | — | `## Automatic loading`：腳本位置、matcher、關閉變數、hook 模式不輸出啟用訊息 |

另外更新兩個 `agents/openai.yaml` 的 `short_description` 與 `session-preferences/README.md`。改完跑 `skill-auditor`。

### Repo 指引：`CLAUDE.md` 與 `AGENTS.md`

部署鏈原本沒有記在 repo 裡，每個 session 都得重新查。這次一併補上：

- `CLAUDE.md` 新增 `## Deployment` 段落：
  - `~/.claude/skills` 是 symlink，指向 `agent-skills-production` worktree（`production` 分支）；main 的改動要合併到 production 才生效。
  - `~/.codex/skills`、`~/.omp/agent/skills` 是 skill-sync 用 rsync 鏡像的副本；production 改動後要先看預覽再跑 skill-sync。
  - 新增或修改的 Codex hook 要在 Codex 裡核准後才會執行。
- 新增 `AGENTS.md`，以相對路徑 symlink 到 `CLAUDE.md`，讓 Codex 在這個 repo 也讀得到同一份指引。不採複製，避免兩份內容不同步。
- `CLAUDE.md` 第一行從「guidance to Claude Code」改成同時涵蓋兩個 runtime，並註明 `AGENTS.md` 是 symlink。其他 Claude 專屬寫法這次不改。

已查證：skill-sync 使用 `rsync -avL`，會把 symlink 展開成實體檔案，所以鏡像目標不會出現斷掉的連結。這是 repo 第一個被 git 追蹤的 symlink；在 Windows clone 時會變成內容只有 `CLAUDE.md` 的純文字檔，目前的環境用不到 Windows，所以不處理。

## 6. Error handling

hook 一律 exit 0，不擋 session 啟動。

| 狀況 | 行為 |
|---|---|
| `AGENT_SESSION_PREFS=off` | 不輸出 |
| `INDEX.md` 讀不到 | 不注入規則；`systemMessage` 顯示缺的路徑 |
| INDEX 列的模組讀不到 | 其他模組照常注入；context 寫明未載入的路徑；`systemMessage` 警告 |
| 抽不到 control-return 的 Rule 區塊 | 不注入；`systemMessage` 警告 |
| 其他例外 | 攔下，輸出 `systemMessage`，exit 0 |

## 7. Testing

1. `tests/test_session_start_hooks.py`（`unittest`，照 repo 現有寫法）：暫存目錄建假 skill 結構、複製腳本、subprocess 執行。涵蓋正常、關閉變數、INDEX 缺、模組缺、Rule 區塊缺，每種驗證輸出為合法 JSON。
2. 對 `~/.claude/skills` 真實路徑餵樣本輸入，確認內容與大小。
3. Claude Code：`claude -p` 問模型收到哪些模組與 control-return 規則；再以 `AGENT_SESSION_PREFS=off` 跑一次確認未注入。
4. Codex：skill-sync 與核准後，用 `codex exec` 做同樣檢查，同時確認 `additional_context_limit` 沒截斷內容。
5. resume 實驗：兩邊各接續一個舊 session，問模型規則是否還在。結果寫回本文件；若未保留，重新討論 matcher。
6. compact：使用者在互動 session 手動 `/compact` 後確認。

## 8. Out of scope

- 自動執行 skill-sync，或自動合併 main 到 production。
- 各 skill 個別的關閉開關。
- 自動偵測非互動 session（`claude -p`、`codex exec`、codex rescue）。這些 session 沒設關閉變數時也會被注入，屬已接受風險。
- 解決 deai-voice 與 `deai-tom` output style 的重疊；以注入開頭的優先序說明處理。
