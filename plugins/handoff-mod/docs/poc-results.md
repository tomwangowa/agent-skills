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
| L3 | band 的數字 hotkey 與 `AskUserQuestion` 的數字衝突嗎？ | `/poc-band`，再請 Claude 呼叫 AskUserQuestion，按 `1` | 提示要不要在等待時隱藏。**已驗證（本機；`AskUserQuestion` 與權限提示），見下一節** |
| L4 | Claude 工作中，計時器呼叫的 `$.ui.ask` 會怎樣？ | 讓 Claude 長時間產出（例如寫 1500 字文章、不用工具），3 秒內 `/poc-ask-timer`；前景 `sleep 30` 在 Tom 的環境會被擋 | 門檻提示只能在閒置時出現，還是可以插話。**已驗證（本機；含不回答），見下一節** |
| L5 | 真實對話的 `/compact`：`command.run compact` 與 `session.compact` 的先後 | 有內容的 session 內 `/compact` | 壓縮前能不能問交接。**事件時序已驗證（本機），見下一節；在 hook 內提問未測** |
| L6 | 真正結束：Ctrl-D、關掉分頁，`session.end` 有沒有跑 | 結束後看 log | 「結束時自動留事實筆記」（D4）可不可行。**已驗證（本機），見下一節** |
| L7 | 非 git 目錄、子目錄啟動、worktree 的 `root()` 與 `repo().root` | 各處 `/poc-facts` | 範圍鍵（交接檔歸屬）的規則。**部分已驗證（本機 headless），見下一節；`/cd` 尚未測** |
| L8 | 與 attention-mod 同時載入 | `--plugin-dir` 各載一次，開 band 與 ask | band 共用、等待訊號重複。**已驗證（本機），見下一節** |

## 本機驗證（Tom 的環境）

日期：2026-10-06 至 07。環境：Tom 的 macOS。Claude Code 版本中途從 2.1.291 更新到 2.1.292：L1 到 L5、L7、L3 第一部分用 2.1.291；權限提示與不回答的補測、L6、L8 用 2.1.292（以各 session transcript 的 `version` 為準）。L7 用 `claude -p "/poc-facts" --plugin-dir …/handoff-poc` 在各目錄各跑一次，由 Claude 在 Tom 的終端機代跑，**不是**互動 session，`surfaces()` 為 `[]`，`/cd` 要互動、沒測。L1 在 Tom 自己開的互動 session 量測。

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

### L3 hotkey 與對話框（`AskUserQuestion`、權限提示；已驗證，本機互動）

band 開著（`/poc-band`），請 Claude 呼叫 `AskUserQuestion`，等選項畫面出現後按數字 `1`。做了兩次，用 transcript 與 log 對時間：

| 次數 | 呼叫 → 回答 | 結果 | 這段期間的 `band press` |
| --- | --- | --- | --- |
| 1 | 16:00:18 → 16:01:03（45 秒） | 第 1 個選項 | 無（計數仍是先前閒置時按的 3 次） |
| 2（確定按的是數字 `1`） | 16:03:21 → 16:03:24（3 秒） | 第 1 個選項 | 無 |

- 問題在等的時候，畫面上沒有 band，只有引擎的選項對話框；band 在回答完才重新出現。這一點只有畫面佐證，探針沒有記 render。
- 數字鍵被對話框吃掉，band 沒有反應。依決策表，「L3：無衝突，只要閒置就顯示 band」成立。
- `hasSurvey` 在問題等待時沒有觀察到（band 當時沒畫出來），回答後是 `false`；型別檔沒有 `survey`、`isWorking` 的說明，沒有證據它是等待訊號，設計不使用它。
- **工具權限提示也無衝突**（補測）。Tom 的全域設定是 `bypassPermissions`，不會跳提示，所以改用 `claude --permission-mode default --plugin-dir …` 開新 session（transcript 的 `permissionMode=default`）。`curl -sI https://example.com` 跳出權限提示，Tom 按數字 `1` 選了 Yes：提示等待時畫面上沒有 band，指令執行了，log 沒有新的 `band press`。同一輪平行呼叫的 `curl` 等了約 8.3 秒才回（bypass 時約 0.8 秒），符合在等人按鍵。
- 這個版本的權限提示有四個選項：`1. Yes`、`2. Yes, and don't ask again for: curl *`、`3. Yes, and switch to auto mode`、`4. No`，不是三個。
- 結論：兩種對話框（`AskUserQuestion`、權限提示）等待時 band 都不在，數字鍵都歸對話框；band 只在閒置時出現。依決策表採「只要閒置就顯示」。
- 同事用預設模式才會碰到權限提示，Tom 自己的環境永遠不會，所以這一項要在非 bypass 的 session 才測得到。
- 閒置時在空白輸入框按 `1` 會立刻觸發按鈕、不需要 Enter，每按一次在 transcript 追加一行 `band press 1` 通知。

### L4 工作中提問（已驗證，本機互動）

第一次嘗試無效：前景 `sleep 30` 被環境擋掉（`Blocked: standalone sleep 30. … use Monitor with an until-loop`），Claude 改成背景執行，回合 7 秒就結束，30 秒內 Claude 其實是閒置的。第二次改成讓 Claude 長時間產出（不用工具）：

| 時間 | 事件 |
| --- | --- |
| 16:09:29 | 送出任務，回合開始 |
| 16:09:47 | `ask(timer) turns=16 answer=同意`（回答完才記，不是彈出時間） |
| 16:10:09 | thinking 結束 |
| 16:10:20 | 輸出完成（6003 個輸出 token） |
| 16:10:21 | `turn.complete` |

- 提問在回合進行中被回答，`ask(timer)` 排在 `turn.complete` 前 34 秒；彈出時間只知道在 16:09:32 到 16:09:47 之間，當時 Claude 在 thinking。
- 回合沒被打斷，文章完整；回答只回到探針，沒有送進 Claude 的對話。
- 提問期間輸入框能不能打字沒有記錄。

**補測：不回答。** 用預設模式的新 session，送出「隨便給我 200 字的文章」，`/poc-ask-timer` 彈出後先不答：

| 時間（UTC） | 事件 |
| --- | --- |
| 02:39:50 | 送出任務 |
| 02:40:02 | 文章輸出完成 |
| 02:40:03 | `turn.complete` |
| 02:40:10 | `ask(timer) turns=2 answer=同意`（回答完才記） |

- `ask(timer)` 排在 `turn.complete` **之後 7 秒**：回合結束時提問還開著，Claude 沒有等它，文章照常完成。**不回答不會卡住工作。**
- `$.ui.ask` 的對話框**不能單獨按數字選**，要用方向鍵加 Enter（Tom 回報）。這跟 L3 的 `AskUserQuestion`（按 `1` 直接選中）不同，原因不明；這段時間 `band press` 沒有新增，band 的 hotkey 沒有搶到按鍵。
- 提問在回合結束後仍然開著，設計要處理「使用者一直沒答、下一個回合又開始」的過期對話框（例如下一個提示要不要取代舊的）。
- 對決策表：技術上「能彈出且不擋工作」成立，但不等於該在工作中彈出。「不回答」也不會卡住工作，所以風險只剩打斷感與過期對話框；第一版建議仍只在 `turn.complete` 後閒置時提示（待 Tom 決定）。
- 附帶：背景指令完成的通知會自己觸發一個回合（16:07:07，沒有使用者輸入），那種回合也會讓 `turn.complete` 觸發，T1 的「閒置」判斷要考慮。

### L5 壓縮（事件時序已驗證，本機互動；手動壓縮）

| 時間 | 事件 |
| --- | --- |
| 16:15:01.985 | 送出 `/compact` |
| 16:15:02.061 | `command.run compact` |
| 16:15:02.102 | `session.compact`，`trigger:"manual"`，帶著要壓縮的 `messages` |
| 16:15:39.964 | transcript 的 `compact_boundary`，`durationMs: 37296`，`preTokens 98031 → postTokens 8562` |

- `session.compact` 在壓縮開始前 41 ms 觸發，摘要在它之後花 37 秒產生。型別檔說明這個 hook 可以改寫 `instructions`／`messages`，或回 `{ skip: reason }` 讓對話維持原樣。
- 壓縮後第一個回應之前 `usage().context` 只有 `window`；回一次話之後 `tokens 52346 / percent 5`。
- 壓縮後引擎自動重新讀了最近寫的 handoff 檔，並還原兩個 skill。只有這一個點，不知道是否對所有最近碰過的檔案都這樣。
- **沒有測：** 在 `session.compact` hook 裡呼叫 `$.ui.ask` 能不能彈出；自動壓縮的 `trigger` 值。所以第四個觸發點「壓縮前」現在只能寫「有機會」，不能寫「可行」。

**對設計的影響：`percent` 會下降。** 壓縮前 `91454 tokens / 9%`，壓縮後 `52346 tokens / 5%`（`postTokens` 只有 8562，其餘約 4 萬應是固定底加上自動還原的內容，沒有逐項核對）。設計裡「再多 10% 再問」是把下一個門檻設成「目前 % ＋ 10」，「這個門檻沒問過」靠記住問過的值；壓縮或 `/clear`（新 session id）之後 `percent` 掉回去，舊的下一個門檻會讓提示在一大段區間都不出現。門檻狀態要在 `session.compact` 與 `/clear` 時重置，或在 `percent` 下降時重新起算。設計文件目前沒有寫這一點。

### D2 的觀察：worktree 的交接檔位置

- 在 worktree（`~/.claude/agent-skills-handoff`）啟動時，交接檔寫進 **worktree 自己**的 `.claude/handoffs/`；主 checkout（`~/.claude/skills`，`repo().root` 指向的地方）沒有新檔。
- 所以預設是**各 worktree 各一份**：在主 checkout 或另一個 worktree 開 session，看不到這份。要跨 worktree 接續，得用 `repo().root` 加 `git worktree list` 去找各處的 `.claude/handoffs/`；設計文件還沒決定要不要這樣做。
- 限制：只有一次寫檔、從 worktree 根目錄啟動。在 repo 子目錄啟動時會寫到哪裡（子目錄、worktree 根、還是別處）沒測；這份檔案由模型依 skill 文字決定位置，不是 mod 控制的，所以內建 skill 要自己明確指定路徑。

### L6 結束方式（已驗證，本機互動）

| 結束方式 | 事件 | `session.end` 的 `reason` | hook 耗時 |
| --- | --- | --- | --- |
| `/exit`（兩個 session） | `command.run exit`，約 1 到 1.4 秒後 `session.end` | `prompt_input_exit` | 1、2 ms |
| `Ctrl-C` 兩次 | 只有 `session.end`，沒有 `command.run exit` | `prompt_input_exit` | 3 ms |
| 直接關終端機分頁 | `session.end` | `other` | 10 ms |
| `Ctrl-D` | 按三次只有畫面往下捲動一格，session 沒有結束 | 無 | 無 |

- 三種真的會結束的方式都觸發 `session.end`，hook 有跑完，log 也寫進去了。依決策表，D4（結束時留事實筆記）技術上可行；寫一個小檔約 10 ms，遠低於所有 `session.end` hook 合計約 1.5 秒的預算。D4 涉及自動寫檔的隱私邊界，仍要 Tom 拍板。
- `/exit` 與 `Ctrl-C` 兩次的 `reason` 都是 `prompt_input_exit`，無法從 `reason` 分辨；`other` 也見於 `-p` 跑完，所以 `other` 不等於「關分頁」。
- 關分頁只測了 Warp 一次。`kill -9`、當機、斷電沒有任何 hook，D4 做不到，設計要接受。
- `Ctrl-D` 在 Tom 的環境不是離開（原因沒查：Warp 吃掉，或 Claude Code 綁成捲動）。計畫原本假設「Ctrl-D 結束」，不成立。
- **探針 log 的缺陷：** `note()` 先讀整個檔案、加一行、再整份寫回，不是附加。同時有多個 session 時會互相覆蓋，A 的 `session.start` 就是這樣沒進 log（transcript 裡有）。關分頁時行程會被殺，transcript 可能來不及寫，log 是唯一證據，所以那一輪是單獨一個 session 測的。以後 PoC 若要同時開多個 session，要改成附加寫入或每個 session 各寫一個檔。

### L8 與 attention-mod 共存（已驗證，本機互動；2.1.292）

`--plugin-dir` 各載 attention-mod 與 handoff-poc，開 band，再 `/poc-ask`：

| 情境 | 結果 |
| --- | --- |
| 寬視窗，閒置 | attention-mod 的面板在右半邊，band 在左半邊，不遮蔽。band 收到的 `viewport` 是扣掉右側面板後的 `72x38`、`bodyColumns=67`（單獨載入時 `115x38`、`110`）。band 的說明文字折成兩行，三個按鈕那一行在 67 欄放得下 |
| 窄視窗，閒置 | attention-mod 切成 inline 模式，面板蓋在輸入框上方；band 只剩 `↓2 more` 與 `[-]` 一行。我的推斷：這一區有行數上限，我們的按鈕排在 attention-mod 的內容之後，被截掉。按 `[-]` 後整個 plugin 區收成一行 `plugin panel hidden · ctrl+x ctrl+a or click to show` |
| 寬視窗，`/poc-ask` | 對話框完整顯示，右側面板不擋。attention-mod 的「需要你」從「目前沒有待回覆訊號」變成「等待狀態不明」，沒有明確亮起 |
| 窄視窗，`/poc-ask` | 對話框完整顯示；attention-mod 的 inline 面板與 band 在對話框等待時都不見（輸入框上方整區被對話框取代），回答後面板回來 |
| 回答之後 | 「需要你」仍是「等待狀態不明」，沒有回到「目前沒有待回覆訊號」（只有一張截圖，不確定是否穩定） |

對決策表的意思：

- 寬視窗並排可行；窄視窗下 band 被擠出可見範圍，所以窄視窗要改用 toast 加指令，或至少不能只靠 band。
- attention-mod 的「外部輸入」會列出我們的 `$.ui.log` 通知（`informational · 引擎`，例如 `handoff-poc: poc: ask answer=同意`）。正式的 handoff-mod 若用 `$.ui.log` 發通知，會灌進 attention-mod 的外部輸入，要克制。
- `$.ui.ask` 不會讓 attention-mod 明確亮起「需要你」，這是 attention-mod 那邊的行為，handoff-mod 沒有依賴。「等待狀態不明」回答後不會復原，若要反映給 attention-mod，由它那邊處理。

### 補驗（未完成，2026-10-07）

決策完成後針對設計裡的未驗證項目加了探針，Tom 決定不再測，所以以下只有 headless（`claude -p`，Claude Code 2.1.292）與一次互動 `/poc-facts` 的資料，**探針改動已還原，沒有進 git**。

| 項目 | 結果 | 限制 |
| --- | --- | --- |
| D4：`session.end` 內讀 `$.session.messages()` | headless 丟錯：`not available in this mode: no session is bound in this process`（REPL 未掛載、沒有 headless session） | **互動 session 結束時是否同樣讀不到沒測。** 這是 D4 的核心假設 |
| D4：`session.end` 內跑 `git status --short` | 76 ms，exit 0（headless） | 只在 headless 量 |
| D4：寫檔後 `chmod 600` | 寫檔加 `chmod` 共 16 ms，檔案權限 `-rw-------`；整個 `session.end` 約 100 ms（headless） | `$.fs.write` 沒有權限參數，0600 要靠寫完再 `chmod` |
| D11：自動偵測使用者語言 | Tom 的互動 session：`$.settings.read().language` 為未設，`LANG=C.UTF-8`、`LC_ALL` 未設。`$.settings.read()` 讀得到 `language`，但 Tom 沒設 | 沒有可靠的自動偵測來源 |

**沒測：** `$.ui.status` 與 `$.ui.toast` 在 attention-mod inline 模式下的實際顯示（D9）、`session.compact` hook 內的 `$.ui.ask` 與回 `{skip}`（T4）、`/cd` 之後的 `root()`（L7）、自動壓縮的 `trigger` 值。這些在設計文件列為實作前要先驗證的風險。

## 清理

PoC 結束、結果寫完後刪除 `poc/`。探針不是產品，不會進 marketplace。
