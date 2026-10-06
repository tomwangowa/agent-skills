# Handoff Mod micro-PoC 結果

日期：2026-10-06。計畫見 [micro-PoC 計畫](superpowers/plans/2026-10-06-handoff-mod-poc.md)，設計見 [Handoff Mod 設計](superpowers/specs/2026-10-06-handoff-mod-design.md)。

## 證據的環境與界限

下表的「已驗證」都在 **Cloud container** 取得：Linux、Claude Code 2.1.291、模型 `claude-sonnet-5-5`（window 1,000,000）、用 pty 驅動真正的互動 session（80／120／170 欄）；標「headless」的是 `claude -p`。**不是 Tom 的 macOS、Warp、預設模型，也沒有 Tom 的 harness。** 標題寫「待本機」的項目還沒做，不能當成已驗證。

探針在 `poc/handoff-poc/`，每個探針都把結果寫進 `$TMPDIR/handoff-poc.log`（沒設 `TMPDIR` 時是 `/tmp/handoff-poc.log`）和 transcript。`claude plugin validate --strict` 通過。

## 已驗證（Cloud）

| 編號 | 問題 | 結果 |
| --- | --- | --- |
| V1 | `context.percent` 是已用還是剩餘？ | **已用**，整數 0–100，對 `window`。一輪回應後 `tokens 36225 / window 1000000 → percent 4`（3.6%，四捨五入；本機 53076 → 5、71711 → 7 也是四捨五入，不是進位）。第一個回應之前只有 `window`，沒有 `tokens`／`percent`。型別檔另註明：壓縮後也要等下一個回應才有；`breakdown` 量的是可能比 `window` 小的壓縮視窗。 |
| V2a | `$.prompt.submit` 能不能送 `/handoff` 之類的指令文字？ | **不能**。文字開頭是 `/` 會被拒絕：「run one with `$.command.run({ command })`」。 |
| V2b | 從 `command.run` hook 裡直接呼叫 `prompt.submit`／`command.run`？ | **會被拒絕**（「would wait on the turn this hook is holding」），要從計時器或之後的事件（如 `turn.complete`）呼叫。 |
| V2c | `$.command.run({command})` 能不能啟動 plugin skill？ | **能**（互動 session，從 `$.clock.after` 計時器呼叫）。skill 展開（`skill.prompt` 觸發）、`prompt.submit` 的 origin 是 `plugin`、transcript 顯示「Prompt from the handoff-poc plugin ❯ /handoff-poc:poc-skill」、模型照 skill 回覆。**plugin skill 的指令名是 `<plugin>:<skill>`。** |
| V2d | `$.prompt.fill({text})` | `{isFilled:true}`，文字出現在輸入框，等使用者按 Enter。 |
| V3a | 內建 `/clear`、`/compact` 會不會進 `command.run`？ | **會**（headless 兩者都會；互動的 `/clear` 也會）。 |
| V3b | `/clear` 的事件順序 | `command.run clear` → `session.end（reason=clear）` → `classic.SessionStart（source=clear，新 session id）`。 |
| V3c | hook 能不能取消 `/clear`？ | **能**。`command.run` 的 `clear` hook 不呼叫 `next`、直接回 `{text}`：沒有 `session.end`、session 沒換。 |
| V3d | `session.end` hook 能做事嗎？ | 寫一行 log 花 **5–13 ms**（`reason=other` 與 `reason=clear`）。預算是所有 `session.end` hook 合計約 1.5 秒（文件）。 |
| V4a | band（`AbovePrompt`）在窄終端機畫得出來嗎？ | **畫得出來**：80 欄 `bodyColumns=75`、120 欄 `115`，`maxRows=14`。三個按鈕 `1: 同意  2: 再多 10% 再問  3: 這個 session 別再問` 單行放得下。 |
| V4b | 數字 hotkey | 空白輸入框單獨按 `1` 觸發按鈕（`band press 1`）。 |
| V4c | `$.ui.ask` | 彈出引擎的對話框：`☐ Plugin <問題>`、選項 `1.`–`3.`，後面自動多 `4. Type something.` 和 `5. Chat about this`；回傳選到的標籤。從計時器、閒置時呼叫也能彈出。 |
| V5 | mod 自己開的 pane | 80 欄：`isPlaced:false`，原因「unasked below 144 columns (80 now)…」；170 欄：`isPlaced:true`。 |
| V6a | session 範圍 | git repo 內：`cwd = root = /home/user/agent-skills`；`repo()` 回 `{root, remote, internal:false, name:null}`；啟動時 `messages=0`。`$.process.run(['git', …])` 取得 toplevel、`--git-common-dir`（`.git`）、HEAD、branch 都正常。 |
| V6b | 啟動事件 | `classic.SessionStart` 的 `source=startup`；`session.start` 的 `interactive` 互動為 `true`、headless 為 `false`；`surfaces()` 互動為 `["terminal"]`、headless 為 `[]`。 |
| V6c | 偵測使用者自己的 handoff | `$.command.list()` 同時列出 `handoff[user]` 與 `handoff-poc:poc-skill[plugin:handoff-poc]`，每筆有 `source`（`builtin`／`plugin`／`user`／`mcp`）與 `plugin`。 |

## 待本機（Tom 的環境）

| 編號 | 要驗的事 | 怎麼做 | 結果決定什麼 |
| --- | --- | --- | --- |
| L1 | 你的模型 window 與 `percent` 跟 `/context` 一致嗎？ | 做一段真實工作後 `/poc-usage`，對照 `/context` | 門檻的預設值（D1）。**已驗證（本機），見下一節** |
| L2 | 用 `$.command.run` 啟動你自己的 `/handoff`（`disable-model-invocation: true`） | `/poc-submit cmd:handoff` | 「有使用者自己的 handoff 就用它」可不可行（D7）。**已驗證（本機），見下一節** |
| L3 | band 的數字 hotkey 與 `AskUserQuestion` 的數字衝突嗎？ | `/poc-band`，再請 Claude 呼叫 AskUserQuestion，按 `1` | 提示要不要在等待時隱藏 |
| L4 | Claude 工作中，計時器呼叫的 `$.ui.ask` 會怎樣？ | 先跑 `sleep 30` 的 Bash，再 `/poc-ask-timer` | 門檻提示只能在閒置時出現，還是可以插話 |
| L5 | 真實對話的 `/compact`：`command.run compact` 與 `session.compact` 的先後 | 有內容的 session 內 `/compact` | 壓縮前能不能問交接 |
| L6 | 真正結束：Ctrl-D、關掉分頁，`session.end` 有沒有跑 | 結束後看 log | 「結束時自動留事實筆記」（D4）可不可行 |
| L7 | 非 git 目錄、子目錄啟動、worktree 的 `root()` 與 `repo().root` | 各處 `/poc-facts` | 範圍鍵（交接檔歸屬）的規則。**部分已驗證（本機 headless），見下一節；`/cd` 尚未測** |
| L8 | 與 attention-mod 同時載入 | `--plugin-dir` 各載一次，開 band 與 ask | band 共用、等待訊號重複 |

## 本機驗證（Tom 的環境）

日期：2026-10-06。環境：Tom 的 macOS、Claude Code 2.1.291。L7 用 `claude -p "/poc-facts" --plugin-dir …/handoff-poc` 在各目錄各跑一次，由 Claude 在 Tom 的終端機代跑，**不是**互動 session，`surfaces()` 為 `[]`，`/cd` 要互動、沒測。L1 在 Tom 自己開的互動 session 量測。

### L7 範圍

| 啟動位置 | `root()` | `repo()` | `git --git-common-dir` | 觀察 |
| --- | --- | --- | --- | --- |
| repo 根目錄（`~/.claude/skills`，main） | = cwd | `{root: ~/.claude/skills, …}` | 相對路徑 `.git` | `root()` 與 `repo().root` 相同 |
| repo 子目錄（`agent-skills-handoff/plugins/handoff-mod/docs`，在 worktree 內） | = cwd（子目錄本身） | `root` 是**主 checkout** `~/.claude/skills` | 絕對路徑 | `root()` **不會**往上推到 repo 根 |
| `git worktree add` 出來的 worktree（`~/.claude/agent-skills-handoff`） | = worktree 路徑 | `root` 是**主 checkout** `~/.claude/skills` | 絕對路徑 `~/.claude/skills/.git` | `repo().root` 在所有 worktree 都相同，`root()` 各自不同 |
| 非 git 目錄 | = cwd | `null` | exit 128 | `git` 指令全部失敗 |

對決策表的意思：

- worktree 的 `root()` 不同、`repo().root` 相同，所以用 `repo().root` 聚合同一個 repo 的交接，`root()` 標示來源 worktree。
- 非 git 目錄 `repo()` 為 `null`，以 `root()` 為鍵，不做新鮮度檢查，清單標示「無法驗證」。
- `root()` 不等於 repo 根，所以「相對 repo 根的路徑」要用 `repo().root` 或 `git rev-parse --show-toplevel` 算，不能拿 `root()`。
- `repo().root` 在 worktree 裡指向主 checkout，不是目前的 worktree。若交接檔放 repo 內 `.claude/handoffs/`（D2），要決定是寫到主 checkout 還是各 worktree 自己的目錄；這點設計文件還沒處理。

### L1 用量對照（已驗證，本機互動）

預設模型 `sonnet` 解析為 `claude-sonnet-5-5`，`window = 1000000`，`/context` 也顯示 `Sonnet 5.5`、`1m`。

| 時間點 | `usage()` 的 `tokens`／`percent` | `/context` | 來源 |
| --- | --- | --- | --- |
| 一個回合後 | 53076／5 | 53.1k／5% | `turn.complete` 自動記的那一行，不是 `/poc-usage` 指令 |
| 之後 | 71711／7 | 71.7k／7% | 手動 `/poc-usage` |

- `tokens` 與 `/context` 一致，`percent` 是對 `window` 的已用百分比，**四捨五入**到整數。依決策表，門檻用 `usage().context.percent`，維持設計。
- 限制：只有兩個點，最大 7%；沒有量到 20% 以上，也沒測壓縮後。第一個點沒有經過 `/poc-usage` 指令。
- 這個環境的固定底（system、tools、memory、skills）約 3%；`/context` 的「Autocompact buffer」33k 另外列，不算在已用 tokens。

### L2 使用者自己的 handoff（已驗證，本機互動）

在 Tom 自己開的互動 session，`/poc-submit cmd:handoff`（`~/.claude/skills/handoff`，`disable-model-invocation: true`）。

| 項目 | 結果 |
| --- | --- |
| 啟動 | 成立。`$.command.run({command:'handoff'})` 回 `{}`，接著 `prompt.submit origin=plugin text=/handoff`，transcript 是 `❯ /handoff`。`$.command.list()` 同時有 `handoff[user]` 與 `anthropic-skills:handoff[user]`，log 分不出展開的是哪一個，從草稿格式看是前者 |
| `skill.prompt` | **不會觸發**（整份 log 計數 0）。Cloud 測 plugin skill 時會；user skill 經 `$.command.run` 啟動只看得到 `prompt.submit`。要偵測 handoff 是否被啟動，不能靠 `skill.prompt` |
| Review Gate | 成立。先顯示完整草稿、問「這樣對嗎」，回覆前沒有寫檔（兩個位置都確認沒有新檔）。整個草稿回合 24 秒 |
| 寫檔 | 確認後寫出 `<worktree>/.claude/handoffs/feat-handoff-mod--20261006-234937.md`。檔名的 `/` 換成 `-`，frontmatter `branch:` 是未 sanitize 的 `feat/handoff-mod`，`assertions` 只用白名單的 `branch_is`、`expect_head` |
| git | 被 `~/.gitignore_global` 第 7 行 `**/.claude/handoffs/` 擋掉，`git status` 看不到 |

對決策表的意思：

- 能啟動、有照格式寫出，所以 D7 **可以**在偵測到 `source:'user'` 的 `handoff` 時優先用，但仍要驗證寫出的 frontmatter。這只代表 Tom 的環境；同事沒有這個 skill，設計文件對 D7 的傾向（一律內建）不因此改變。
- 「Review Gate」只擋使用者有看到並糾正的內容。這次草稿的 VERIFIED 有一句「我看過 diff」，收集步驟只跑了 2 個 shell 指令、沒有 `git diff`，這句沒有依據，使用者直接回「寫檔」，原句照樣寫進檔案。內建 `handoff-mod:handoff` 如果要擋這類錯，得在 skill 裡明確限制 VERIFIED 只能列這個回合實際跑過的指令。

### D2 的觀察：worktree 的交接檔位置

- 在 worktree（`~/.claude/agent-skills-handoff`）啟動時，交接檔寫進 **worktree 自己**的 `.claude/handoffs/`；主 checkout（`~/.claude/skills`，`repo().root` 指向的地方）沒有新檔。
- 所以預設是**各 worktree 各一份**：在主 checkout 或另一個 worktree 開 session，看不到這份。要跨 worktree 接續，得用 `repo().root` 加 `git worktree list` 去找各處的 `.claude/handoffs/`；設計文件還沒決定要不要這樣做。
- 限制：只有一次寫檔、從 worktree 根目錄啟動。在 repo 子目錄啟動時會寫到哪裡（子目錄、worktree 根、還是別處）沒測；這份檔案由模型依 skill 文字決定位置，不是 mod 控制的，所以內建 skill 要自己明確指定路徑。

## 清理

PoC 結束、結果寫完後刪除 `poc/`。探針不是產品，不會進 marketplace。
