# Handoff Mod 設計

日期：2026-10-06  
狀態：**草案，Tom 尚未確認。** 標「待決」的項目由 Tom 決定；標「未驗證」的行為 PoC 沒測到。  
plugin 暫名 `handoff-mod`，面板與提示的繁體中文文案暫定「接著做」。  
證據：[micro-PoC 結果](../../poc-results.md)（Cloud 與 Tom 本機實測：macOS、Warp、Claude Code 2.1.291 至 2.1.292）；驗證計畫：[micro-PoC 計畫](../plans/2026-10-06-handoff-mod-poc.md)。

## 目的與範圍

中斷工作後重開 session，多數人不知道怎麼交接；沒有自己 harness 的同事更是如此。本 plugin 做兩件事：

1. 在**會丟失狀態的時刻**（context 快滿、要 `/clear`）提示並協助寫交接檔。
2. 下次**啟動新 session** 時，列出「上次未完成、你可能想接」的項目，由使用者選擇接續。

這不是活動日誌（「最近幾天做了什麼」），不是稽核證據，也不跨機器同步。

**第一版包含：** 內建 skill、門檻觸發、`/clear` 攔截、啟動讀回、交接檔格式與新鮮度檢查、認領。  
**第一版不含：** 見最後「不做的事」。

## 使用者與前提

- 同事沒有 `handoff`、`activity-logger` 之類的 skill → plugin **自帶** skill，裝一次就有。
- 沒有交接檔時，mod 什麼都不畫、不呼叫模型，成本為零。
- 公司可能用 managed settings 限制 mod（文件有 `allowManagedModsOnly`、`allowManagedHooksOnly`、`disableAllHooks`）→ 這種環境只剩手動呼叫 skill；是否仍可用沒有查證，需向同事確認。
- Mod 不在 sandbox，以使用者權限執行；安裝說明要請使用者先看過 `hooks/`。

## 已查證的平台事實

來源與環境見 `poc-results.md`。標「本機」的在 Tom 的環境取得（macOS、Warp、預設模型 `claude-sonnet-5-5`），其餘來自 Linux container。

| 事實 | 對設計的影響 |
| --- | --- |
| `usage().context.percent` 是已用百分比（整數），對模型 `window`（此環境 1,000,000）；第一個回應之前、壓縮之後到下一個回應之前沒有值。本機：與 `/context` 一致，四捨五入；壓縮後會下降（9% → 5%） | 門檻以「已用 %」定義；沒有值時不觸發。**同一個 % 在不同模型是不同的絕對 token 數**；壓縮與 `/clear` 後 % 會往下掉，記住的「下一個門檻」要重置 |
| `prompt.submit` 不能送 `/` 開頭文字；`prompt.submit`／`command.run` 不能從 `command.run` hook 內呼叫 | 用 `$.command.run({command})`，並從計時器或之後的事件呼叫 |
| plugin skill 的指令名是 `<plugin>:<skill>`；`$.command.list()` 回傳每筆的 `source`（`builtin`／`plugin`／`user`／`mcp`） | 內建 skill 叫 `handoff-mod:handoff`，不會與使用者自己的 `/handoff` 衝突；可偵測使用者自己的 handoff；偵測「handoff 是否被啟動」要看 `prompt.submit`，不能靠 `skill.prompt`（本機：user skill 經 `$.command.run` 啟動不觸發它） |
| `$.prompt.fill({text})` 把文字放進輸入框 | 「接續」只填入，由使用者按 Enter |
| 內建 `/clear`、`/compact` 會進 `command.run`；hook 不呼叫 `next`、直接回 `{text}` 可取消 `/clear` | 可以做「先交接再清除」 |
| `/clear` 順序：`command.run` → `session.end(reason=clear)` → `classic.SessionStart(source=clear，新 id)` | 啟動讀回要接 `classic.SessionStart`，不是 `session.start` |
| band（`AbovePrompt`）在 80 欄畫得出來；空白輸入框單獨按數字會觸發 band 的 `hotkey`，不需 Enter（本機） | 門檻提示與啟動清單用 band |
| 任何對話框（`AskUserQuestion`、權限提示、`$.ui.ask`）等待時，輸入框上方整區（band、attention-mod 的 inline 面板）都消失，數字鍵歸對話框，band 沒有搶到按鍵（本機） | band 只在閒置時畫，不需要為對話框特別隱藏 |
| 與 attention-mod 同載入（本機）：寬視窗並排不遮蔽，band 收到的 `viewport` 是扣掉右側面板後的寬度（72 欄時 `bodyColumns=67`）；窄視窗 attention-mod 切成 inline，band 被擠到 `↓2 more` 之後看不到 | 寬視窗用 band，按鈕列要在 67 欄內放得下；窄視窗改用 toast＋指令（D9） |
| attention-mod 的「外部輸入」會列出 `$.ui.log` 的通知（本機） | 正式 mod 的 `$.ui.log` 要克制，只留對使用者有意義的訊息 |
| mod 自己開 pane：80 欄 `isPlaced:false`，170 欄 `true`（門檻 144 欄） | 不用 pane |
| `$.ui.ask` 彈出引擎的提問對話框，2–4 個選項，另附「Type something」與「Chat about this」，被關掉或 `-p` 時 reject。本機：對話框不能單獨按數字，要方向鍵加 Enter；使用者不回答不會卡住回合，對話框在 `turn.complete` 之後仍開著 | `/clear` 攔截用它；reject 一律視為取消；要處理過期的對話框 |
| `session.end`：本機 `/exit`、`Ctrl-C` 兩次、關分頁都會觸發（`reason` 分別是 `prompt_input_exit`、`prompt_input_exit`、`other`），hook 寫一行檔案 1–10 ms；`Ctrl-D` 在 Tom 的環境不是離開；`kill -9`、當機沒有 | 結束時留事實筆記技術上可行（D4） |
| `session.compact` 在壓縮開始前約 41 ms 觸發（`trigger:"manual"`），帶著 messages，可回 `{skip}` 否決；在這個 hook 裡能否 `$.ui.ask` 未驗證（本機） | T4 有機會，待驗 |
| `repo()` 回 `{root, remote, …}`，不在 git 內是 `null`；worktree 時 `repo().root` 是主 checkout，`session.root()` 是 worktree 自己；從 repo 子目錄啟動時 `session.root()` 就是子目錄，不會往上推（本機） | 範圍鍵見下；git repo 內以 `git rev-parse --show-toplevel` 為基準，不直接用 `session.root()`（D10） |

## 元件

### 1. 內建 skill：`handoff-mod:handoff`

沿用 Tom 的 `handoff` skill 的做法，但砍到最小，不依賴 `activity-logger` 等其他 skill：

1. 唯讀收集：branch、`git status`、近期 commit、當前對話。
2. 草擬交接（格式見下），**完整顯示給使用者確認，未經確認不寫檔**。這道關卡擋掉 AI 把沒驗過的事標成已驗證。
3. 確認後寫入交接目錄，回報完整路徑。
4. 指示明寫：不寫入金鑰、token、客戶資料；「已驗證／未驗證」兩欄必填，並標明這是 AI 自述；「已驗證」只能列這個回合實際跑過的指令或讀過的檔案，並寫明是哪個指令（本機 L2：Tom 的 `handoff` 曾把沒跑過的「我看過 diff」標成已驗證，Review Gate 沒擋住）。寫檔路徑由 skill 明確指定（`git rev-parse --show-toplevel` 加 `.claude/handoffs/`），不讓模型自己猜（D10）。

skill 不依賴 mod；沒有 mod 時使用者仍可手動 `/handoff-mod:handoff`。

### 2. 觸發器（`hooks/trigger.js`，純函式）

`decideTrigger(state, usage, signals)` 回傳 `ask`、`wait` 或 `none`，不碰 `$`，可單獨測試。

| 觸發點 | 條件 | 介面 |
| --- | --- | --- |
| T1 門檻 | `percent` 有值且 ≥ 門檻；`turn.complete` 之後閒置、沒有等待；有未完成跡象；本 session 沒被抑制；這個門檻沒問過 | band，三個按鈕；窄視窗且有 attention-mod 時改 toast＋指令（D9） |
| T2 `/clear` | 互動 session；`turns() > 0`；有未完成跡象 | `$.ui.ask`，三個選項 |
| T3 手動 | 使用者自己下 `/handoff-mod:handoff` | 無，skill 直接執行 |
| T4 壓縮前 | 有機會：`session.compact` 在壓縮前觸發且可否決；hook 內 `$.ui.ask` 未驗證 | 待驗 |

**未完成跡象**（假設，未驗證）：本 session 有成功的 `Edit`／`Write`／`NotebookEdit`，或 `git status` 不乾淨。純問答的 session 不需要交接，沒有這個條件使用者會一直被問。

**T1 的三個選項：**

| 鍵 | 動作 |
| --- | --- |
| 1 同意 | 開始交接（見下） |
| 2 再多 10% 再問 | 隱藏 band；下一個門檻 = 目前 % ＋ 10 個百分點 |
| 3 這個 session 別再問 | 這個 session 不再提示；記在記憶體，`/clear` 後視為新對話，重新開始 |

不操作等於暫緩：band 保持顯示，不重複彈出；`/clear`、新 session 時消失。

**門檻狀態會重置：** `percent` 在壓縮與 `/clear` 後會下降（本機：9% → 5%），所以「下一個門檻」與「這個門檻沒問過」要在 `session.compact`、`/clear`（新 session id）時清掉；或在 `percent` 低於上次問過的值時重新起算。否則舊的下一個門檻會讓提示在一大段區間都不出現。

**T2 的三個選項：** 先交接再清除／直接清除／取消。選「先交接」時 hook **不呼叫 `next`**，回 `{text}` 說明「已暫停清除，交接完成後請再下 `/clear`」，並從計時器開始交接。「直接清除」呼叫 `next(e)`；取消、關閉、reject 都回 `{text}` 不執行。`-p` 或非互動時不攔截。

**同意之後：** 從計時器呼叫 `$.command.run({command})`。`command` 是 `handoff-mod:handoff`，或在 D7 選用且偵測到時為使用者自己的 `handoff`。

**不信任「已寫好」：** 之後的 `turn.complete`，mod 掃描交接目錄找 mtime 晚於開始時間的新檔並解析 frontmatter；成功才 toast 顯示路徑，並把目錄記進索引；否則顯示「未偵測到有效交接檔」。

### 3. 啟動讀回

- **時機：** `classic.SessionStart`，`source` 為 `startup` 或 `clear`（`resume`、`fork`、`compact` 不顯示，對話已有脈絡）；互動 session；`turns() == 0`。
- **來源：** 目前 worktree（`git rev-parse --show-toplevel`）的交接目錄；`repo().root` 不同時再加上主 checkout 的目錄；其他 worktree 的目錄靠索引（`$.store` 的目錄清單，最多 20 個，逐一確認存在）或 `git worktree list` 找到（D2）。
- **排序：** 同 `root` 優先，其次同 `repo`，其餘依 `created` 由新到舊。預設展開 3 筆，其餘折疊成「還有 N 筆」。創建超過 14 天的預設折疊。
- **每筆顯示：** 任務（≤80 字）、branch、多久以前、新鮮度事實、「下一步」第一行（≤120 字）。
- **按鈕：** 接續、略過。「略過」只對這個 session 有效，不改狀態。
- **介面：** band。跟 attention-mod 共用 band 時，把自己的內容與 `next(e)` 的結果並排（探針已這樣做；共存待本機 L8）。
- **接續：** `$.prompt.fill({text})`，文字是「請先讀 `<路徑>`，驗證其中前提是否仍成立，再接續『下一步』」。只放路徑，不放整份內容。使用者按 Enter 才送出。

### 4. 交接檔格式（schema 1）

位置與檔名：`<root>/.claude/handoffs/<branch 淨化>--<YYYYMMDD-HHMMSS>.md`（沒有 git 時 branch 用 `no-branch`）。

```markdown
---
schema: 1
root: /abs/project/root
repo: /abs/repo/root        # 不在 git 內則省略
branch: feat/login-timeout  # 沒有則省略
head: 781ac6b               # 沒有則省略
created: 2026-10-06T18:30:00+08:00
task: 修正登入逾時
status: in-progress         # in-progress | blocked | ready-for-review
---

## 任務
## 已完成
## 未完成
## 下一步
## 前提（人工確認）
## 規矩（不能違反）
## 已驗證／未驗證（AI 自述）
```

**讀取規則：** 只要求 `status` 與 `created`；其餘缺了就不顯示該項；不認得的欄位忽略。為了相容 Tom 現有的 `handoff`，`worktree` 視為 `root` 的別名；`assertions` 第一版忽略。

**內容是資料，不是指令：** 面板只顯示固定幾個欄位，去除控制字元與 ANSI 碼並限制長度；接續提示只引用路徑；mod 不執行檔案裡的任何內容。

**檔案寫完就不再改。** 之後的狀態變化存在 `$.store`（見 6），不去改檔案，避免非原子寫入造成的毀損。

### 5. 新鮮度（`hooks/freshness.js`）

只在 `repo()` 非 null 且檔案有 `head`／`branch` 時做，全部用 `$.process.run(['git', …])`，不呼叫模型。結果是**事實**，不是結論：

- 「branch `feat/x` 已不存在」
- 「交接後這個 branch 多 12 個 commit」
- 「交接的 HEAD 已包含在預設分支」

任何一個 git 指令失敗就省略該行。非 git 目錄顯示「無法驗證」。

### 6. 生命週期與認領

有效狀態 = `$.store` 的覆寫值，沒有就用檔案的 `status`。

| 轉換 | 觸發 |
| --- | --- |
| in-progress／blocked／ready-for-review → resumed | 使用者按「接續」 |
| → done／abandoned | 使用者用指令（第一版不做按鈕） |

**認領：** 按「接續」時寫 `$.store` 的 `claim:<id> = {sessionId, at}`，**寫完再讀一次**確認自己是贏家（`store` 的 get 後 set 不是原子）。輸家顯示「另一個 session 正在接續」。認領 12 小時後失效，避免 session 當機留下死鎖。

### 7. 範圍鍵

- git repo 內：基準 `base = git rev-parse --show-toplevel`（該 worktree 的頂層）；不在 git 內：`base = $.session.root()`。`session.root()` 在子目錄啟動時就是子目錄，不能直接當基準（L7）。`repo = $.session.repo()?.root ?? null`。
- **不需要是 git repo**：非 git 目錄以 `root` 為鍵，沒有新鮮度檢查，清單標示「無法驗證」。
- worktree：每個 worktree 有自己的目錄（`base` 不同，L2 實測 skill 寫進 worktree 自己的 `.claude/handoffs/`）；`repo().root` 相同的交接在清單中標示關聯。
- 從 `~` 啟動或專案不明：只用 `root` 比對，不猜。
- session 中途 shell `cd` 不會移動 `root()`；`/cd` 未驗證。以寫檔當下算出的 `base` 為準。

**交接檔位置（待決 D2）：** 預設放 `<root>/.claude/handoffs/`，在 git repo 內檢查是否已被忽略，沒有就寫進 `$(git rev-parse --git-path info/exclude)`，避免弄髒同事的 `git status`。

## 資料流

```text
turn.complete / session.measure ─▶ usage ─▶ decideTrigger ─▶ band（1／2／3）
/clear ─▶ command.run hook ─▶ ui.ask ─▶ 先交接（不 next）｜直接清除（next）｜取消
同意 ─▶ clock.after ─▶ $.command.run(handoff) ─▶ 一個回合 ─▶ turn.complete ─▶ 驗證新檔 ─▶ toast＋索引
classic.SessionStart(startup｜clear) ─▶ 掃描 ─▶ 解析 ─▶ 新鮮度 ─▶ 排序 ─▶ band（接續／略過）─▶ prompt.fill
```

## 失敗與降級

| 狀況 | 行為 |
| --- | --- |
| `percent` 沒有值 | 不觸發 |
| `$.ui.ask` reject（關掉、`-p`） | `/clear` 視為取消；`-p` 不攔截 |
| 交接回合沒寫出有效檔案 | 提示「未偵測到有效交接檔」，不標成功 |
| 交接檔格式不合 | 跳過該檔，不影響其他 |
| git 指令失敗或逾時 | 省略該行新鮮度事實 |
| 目錄不存在或讀取失敗 | 當作沒有交接 |
| `$.store` 讀寫失敗 | 不認領、不覆寫狀態；仍可接續，只是不防重複 |
| 任何 hook 內部錯誤 | `try/catch`，不影響主 session（沿用 attention-mod 的被動觀察原則） |

## 待決（Tom）

| 編號 | 問題 | 我的傾向 |
| --- | --- | --- |
| D1 | 門檻的語意與預設值。你原話是「剩餘低於 60%」，等於已用 > 40%；已用 40% 在 1M window 是 40 萬 token，在 200k 模型只有 8 萬 | 以「已用 %」定義、可設定（L1：`percent` 與 `/context` 一致，可用）；預設值仍待你定。測試階段用環境變數 `HANDOFF_THRESHOLD_PCT` 覆寫，測試時設 `10`（1M window 下新 session 約 4%，10% 約十萬 token，不會一開始就達標）；其他觸發條件不因測試而繞過 |
| D2 | 交接檔放 repo 內 `.claude/handoffs/`（跟著 worktree、刪 repo 就沒了）還是使用者目錄（不污染 repo、換機不跟） | repo 內，加 `.git/info/exclude`。L2 實測：skill 寫進 worktree 自己的 `.claude/handoffs/`，各 worktree 各一份；要不要跨 worktree 聚合（`repo().root` 加 `git worktree list`）也請決定 |
| D3 | `/clear` 在沒有未完成跡象時也要問嗎？取消 `/clear` 的做法（不呼叫 `next`）你能接受嗎？ | 沒有跡象就直接放行；取消可接受，文案要清楚 |
| D4 | 結束時用 `session.end` 自動留一份只含事實的接續筆記（最後一個要求原文、最後一段話原文、branch、有改動的檔案），不呼叫模型 | L6 已確認 `/exit`、`Ctrl-C` 兩次、關分頁都觸發 `session.end`，技術上可行（寫檔約 10 ms）；`kill -9`、當機沒有。自動寫檔牽涉隱私邊界，要你拍板；我的傾向仍是第一版不做 |
| D5 | 要不要記錄「交接寫了幾次、最後接續了幾次」來判斷有沒有價值？這需要持久化 | 要，但只放 `$.store`，本機計數，不外傳 |
| D6 | plugin 與 skill 的名稱（暫 `handoff-mod`、`handoff-mod:handoff`） | — |
| D7 | 偵測到使用者自己的 `handoff` 時，優先用它還是一律用內建？ | 一律內建；你自己的 skill 格式只有 Tom 一個人保證相容。L2：你的 `handoff` 能由 `$.command.run` 啟動、Review Gate 與寫檔都成立，但不觸發 `skill.prompt`，理由不變 |
| D8 | 同事是否都讀繁體中文？介面字串要不要預留抽出 | 先繁中，字串集中在一個檔 |
| D9 | 窄視窗且有 attention-mod 時，band 被擠出可見範圍（L8），門檻提示怎麼辦：toast＋指令，還是只在寬視窗提示？ | toast＋指令（`/handoff-mod:handoff`）；寬視窗用 band |
| D10 | 交接目錄的基準：git repo 內用 `git rev-parse --show-toplevel`（每個 worktree 一份），還是 `session.root()`（從子目錄啟動會各有一份，L7）？ | 用 toplevel；不在 git 內才用 `root()` |

## 驗證與測試

- **純函式用 `claude plugin test` 單元測：** `decideTrigger`、frontmatter 解析、排序、新鮮度事實的格式化、文字淨化。先寫會失敗的測試。測試不呼叫模型、不跑 git（git 以注入函式替代）。
- **事件接線由實機驗證：** attention-mod 的經驗是測試 kit 無法端到端觸發部分事件，接線只能靠程式碼審查與實機。哪些事件在 `handoff-mod` 的測試 kit 可觸發，**沒有查證**。
- **實機劇本：** 門檻提示三個選項各走一次；`/clear` 三條路；兩個終端機同時接續同一份；worktree；非 git 目錄；有交接檔與沒有交接檔的啟動；交接回合沒寫出檔案。
- 交接內容的準確度要用真實 session 人工抽查，不在自動測試範圍。
- **PoC 沒測到的：** `/cd` 之後的 `root()`、`session.compact` hook 內的 `$.ui.ask`、自動壓縮的 `trigger` 值、Warp 以外的終端機、同事的環境（版本、managed settings）。

## 不做的事

活動日誌或「最近做了什麼」、跨機器同步、稽核用途的證據保證、不經使用者確認就寫檔（D4 除外且未決）、由 mod 修改交接檔、`model.fork` 起草交接（日後可選）、`/compact` 攔截（待 L5）、跨 agent、檔案內 `assertions` 的自動檢查。

## 來源

- [Use the mods API](https://code.claude.com/docs/en/plugins/mods/api)、[Mods reference](https://code.claude.com/docs/en/plugins/mods/reference)、[Draw in the interface](https://code.claude.com/docs/en/plugins/mods/interface)、[React to events](https://code.claude.com/docs/en/plugins/mods/events)。
- 本機型別（Claude Code 2.1.291 產生，已 gitignore）優先於公開文件。
- 既有設計慣例：[Attention Mod 設計](../../../../attention-mod/docs/superpowers/specs/2026-10-03-attention-mod-design.md)。
