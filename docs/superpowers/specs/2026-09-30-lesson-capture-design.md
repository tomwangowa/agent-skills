---
title: Lesson capture skill (/lesson)
date: 2026-09-30
status: approved
---

# Lesson capture skill (`/lesson`)

## 1. Goal

在設計、開發、debug 的過程中，隨時把 lesson learned（使用者的與 agent 的）記下來，並且讓之後的 session 真的讀得到。

讀者有兩種：

- 使用者自己：在筆記工具（例如 Obsidian）裡查閱，需要完整的來龍去脈。
- 各個 coding agent：session 開始時自動載入，只需要短而可執行的規則。

本設計的重點是第二種。lesson 寫進去卻沒人讀，這個機制就沒有價值。

## 2. Confirmed decisions

- 以 agent 自動載入為主，使用者查閱為輔；一份檔案同時服務兩者。
- 由 agent 在自然停頓點主動提議，使用者確認才寫入。不自動寫入。
- 預設私有，存在本機的 lesson 資料夾；要分享的另外用 `promote` 升級成專案文件。
- 資料夾位置由設定檔決定，不假設使用者用 Obsidian。
- 資料不放在 skills repo（此 repo 會公開同步），skill 只放流程與腳本。
- 每條 lesson 一個獨立檔案，以新增為主，避免雲端同步資料夾出現衝突副本。
- 載入策略：只載入「全域」加「目前專案」範圍的短版，設上限。
- 所有 agent 以同一支腳本載入（指令呼叫），不依賴各 agent 的 hook 機制。
- 載入結果用一行狀態讓使用者看得見，agent 在第一則回覆原樣帶出。
- 遷移範圍只有現有 memory 中 `feedback` 類型的檔案。

## 3. Architecture

```
  使用者或 agent 說「記這條」
          │
          ▼
   /lesson（skill，流程）
          │ 寫入
          ▼
   lessons_dir（設定檔指定的資料夾）   每條一個檔案
          ▲
          │ 讀取、篩選、套上限
   lesson digest（腳本）
          ▲
          │ 開工第一個動作執行
   Claude / Codex 等 agent
```

### 3.1 進 repo 的檔案

- `lesson/SKILL.md`：流程與規則。
- `lesson/scripts/`：digest 與輔助腳本。
- `lesson/config.example.json`：設定範例，只放佔位值。
- `lesson/templates/entry-snippet.md`：agent 入口檔要加的片段範本。

實際的 `config.json` 列入 `.gitignore`。

### 3.2 不進 repo 的內容

lesson 資料夾本身、`config.json`、任何個人路徑與專案名稱。

### 3.3 實作語言

腳本使用 Python 3，只用標準函式庫。理由是 frontmatter 解析與上限計算用 shell 寫會很脆。使用者環境需要有 `python3`。

## 4. Lesson file format

檔名：`YYYY-MM-DD-<slug>.md`，`slug` 只含 `[a-z0-9-]`。

```
---
rule: 呼叫 X API 不能只看 status，要檢查 body 的 error code
scope: global            # global 或 project
project: my-app          # 只有 scope 是 project 時才有
status: active           # active 或 retired
created: 2026-09-30
by: claude               # claude、codex、gemini 或 user
migrated_from: <原檔名>  # 只有遷移來的才有
---
## 為什麼
（一兩句）

## 背景
（長版來龍去脈，agent 不會載入）
```

規則：

- `rule` 必須是一行、能照著做的句子，不超過 120 字。寫入時檢查，超過或不像規則就退回改寫。
- digest 只讀 frontmatter，不解析正文。
- 檔案使用純 markdown，不使用 wikilink 或特定筆記工具的語法。
- 寫入前掃描是否含有疑似金鑰或 token 的字串，有就擋下。

## 5. Commands

| 指令 | 作用 | 會改動的內容 |
|---|---|---|
| `/lesson setup` | 首次設定：選 `lessons_dir`、偵測 agent 入口檔、顯示要加的片段，確認才寫 | 設定檔、入口檔（逐檔確認） |
| `/lesson add [內容]` | 起草、確認、寫入新檔 | 新增一個檔 |
| `/lesson list [專案]` | 列出有效的 lesson 與額度使用量；列出疑似衝突副本 | 無 |
| `/lesson promote <id>` | 升級成專案文件：去識別化草稿、給使用者看、確認才寫 | 專案文件 |
| `/lesson retire <id> [原因]` | 把 `status` 改成 `retired` | 只改該檔的 `status` |
| `/lesson review` | 找重複、過長、可能過期的 lesson，逐條提議合併或淘汰 | 逐條確認後才改 |
| `/lesson migrate` | 一次性遷移 `feedback` 檔（見第 9 節） | 新增檔案 |

沒有 `config.json` 時，除 `setup` 外的子指令一律提示先執行 `setup`，不猜路徑。

`retire` 是「只新增不回頭改」原則的唯一例外：它由使用者主動下達，頻率低，同時多處修改同一檔的機率很小。

## 6. Capture flow

新增一條 lesson，不論由使用者叫出或由 agent 提議，走同一條路：

1. 起草：在一則訊息裡給出 `rule`、範圍（全域或哪個專案）、一兩句原因。
2. 使用者回應：好、改、不記。
3. 確認後才寫入。

`rule` 磨不成可執行的句子時不記，長篇經過留在筆記工具當背景。

### 6.1 提議時機

只在自然停頓點提議，例如 bug 修好並驗證過、一個任務完成。條件限定三種：

- 踩過坑並修好。
- 原本的假設被證明是錯的。
- 使用者糾正過 agent。

一次停頓點最多提兩條，多的由 agent 挑最有通則性的。不在追查到一半時打斷。

### 6.2 收工時的合併

收工時的詢問由 `activity-logger` 的 `SKILL.md` 負責：它在收工流程中呼叫 `lesson` 的提議步驟，把 lesson 提議與活動記錄合成同一則訊息，使用者只回答一次。邏輯只放在這一處，agent 入口檔的收工規則不需要修改。

## 7. Digest behavior

`lesson digest --project <名稱>`：

- 輸出第一行固定為狀態行：`lessons: 全域 N 條、專案 M 條`。
- 之後每條一行：`- [全域] <rule>` 或 `- [專案] <rule>`。
- 只納入 `status: active`，且範圍為全域或符合目前專案的檔案。
- 專案名稱取 git 根目錄的資料夾名稱；不在 git 裡就用目前資料夾名稱。同名的不同專案會被視為同一個，此限制先接受。
- 上限預設全域 20 條、專案 10 條，可在 `config.json` 調整。超過時全域優先，同一範圍內以建立日期新的優先。

腳本永遠以成功狀態結束，不擋 session 開工，但不得靜默失敗：

| 情況 | 狀態行 |
|---|---|
| 沒有 `config.json` | `lessons: 尚未設定，請執行 /lesson setup` |
| 資料夾讀不到 | `lessons: ⚠ 讀不到資料夾` |
| 有檔案但載入 0 條（全部 retired 或格式壞掉） | `lessons: ⚠ 找到 N 個檔案，載入 0 條` |
| 有無法解析的檔案 | 照常載入其餘，另加 `⚠ 略過 N 個` |
| 疑似衝突副本（檔名帶 `(1)` 或 `conflicted copy`） | 略過並警告 |
| 超過上限 | 載入到上限為止，並印 `⚠ 已超過上限，請執行 /lesson review` |

## 8. Agent entry points

`templates/entry-snippet.md` 的內容，由 `setup` 填入腳本的實際位置後，加到各 agent 的全域入口檔：

```
## Lessons
- 開工第一個動作：執行 `<script> digest`，並在第一則回覆開頭原樣帶出輸出的第一行。輸出的規則本 session 都要遵守。
- 遇到「踩坑修好」「假設被推翻」「被使用者糾正」時，在自然停頓點提議記錄，一次最多兩條，使用者確認才寫（流程見 /lesson）。
- 沒有 /lesson 可用時，把 JSON（rule、scope、project、why、background、slug）用標準輸入傳給 `<script> add --json -` 寫入；rule 限一行、不超過 120 字。
```

`<script>` 是 `python3 <腳本的絕對路徑>`，由 `setup` 填入。第三條是給讀不到 `SKILL.md` 的 agent 用的（例如還沒安裝這個 skill 的 agent），所以寫入方式要直接放在入口檔裡。

| 入口檔 | 處理 |
|---|---|
| `~/.claude/CLAUDE.md` | 加上述片段 |
| `~/.codex/AGENTS.md` | 加上述片段 |
| `~/.gemini/GEMINI.md` | 使用者不使用 Gemini，本版不處理 |
| 其他（例如 omp、Cursor） | 本版不處理 |

`setup` 只寫入使用者逐檔確認過的入口檔。

## 9. Migration

`/lesson migrate`：

- 來源預設為目前專案的 memory 資料夾中的 `feedback_*.md`，可用 `--from` 指定其他資料夾。`project`、`reference` 類型略過。
- 原檔的 `Why`、`How to apply` 原樣放入新檔的「背景」。
- `rule` 由 agent 起草。先給使用者看對照表（原檔、新 rule、範圍猜測），使用者逐條調整後才寫入。範圍只給猜測，不替使用者決定。
- 每個新檔記錄 `migrated_from`，重跑不會產生重複的 lesson。
- 不修改、不刪除原檔。搬完後原檔仍會被內建 memory 載入，同一規則在上下文中暫時出現兩次。原檔的處理在確認 digest 載入正常之後另外詢問；建議移到備份資料夾，不直接刪除。

## 10. Testing

- 腳本測試：以假資料夾測範圍篩選、上限取捨順序、第 7 節每一種出錯情況、`retired` 不載入、衝突副本略過、`migrate` 重跑不重複、`rule` 超長被擋。測試寫法比照 `activity-logger/tests` 的 shell 測試。
- 隱私掃描：推送前掃描個人路徑、email、資料夾位置與專案名稱是否漏入。
- 手動驗收：四個 agent 各開新 session，確認第一則回覆帶出狀態行。
- 完成 skill 後執行 `skill-auditor`；commit 前依風險等級執行 `code-review-claude`；commit 需使用者明確同意。

## 11. Out of scope

- Claude hook 自動注入、MCP 查詢；上線後觀察到 agent 跳過載入指令再評估。
- omp、Cursor、Gemini 入口。
- 自動判斷 lesson 是否過期或很少被用到；淘汰由 `/lesson review` 加使用者判斷。
- 與 LLM Wiki 整合；lesson 資料夾不會被 wiki 整理程式掃到。
- `promote` 的去識別化只做提示，不保證乾淨。
- 同名專案的覆寫機制、Windows 路徑。

## 12. Assumptions and verification

### Results (2026-09-30)

- Codex（`codex exec`，3 次）：3/3 在第一個動作就執行 digest，並把狀態行當成獨立訊息先顯示，之後才回答。最後一則回答沒有重複那一行（`-o` 只存最後一則訊息）。沒有權限或 sandbox 阻擋；此環境為 `approval_policy = "never"` 加完整檔案權限。
- Claude（`claude -p`，3 次）：3/3 第一行就是狀態行，沒有權限提示；主要設定檔為 `bypassPermissions`。
- Gemini：使用者不使用，未測，本版不處理。
- 同步資料夾：使用者說明其雲端硬碟為鏡像模式，檔案常駐本機，串流（僅線上）情境不適用；此為使用者說明，未另行驗證。嘗試把測試檔設成僅線上時未生效（檔案沒有 `dataless` 旗標），所以串流模式下的讀取行為仍未實測。

### 尚未驗證

- 若日後改用串流（僅線上）模式，腳本不會讀到尚未下載完成的空檔。目前的保護是 digest 會在狀態行顯示「⚠ 略過 N 個」，不會靜默失敗。
- 以預設權限模式啟動的 Claude 設定檔，digest 指令是否會在每次開工跳出權限詢問；需要為該設定檔加一條允許規則（實作計畫 Task 9）。

上線後需要觀察：agent 是否穩定在第一則回覆帶出狀態行；沒有出現代表該次跳過了載入指令。
