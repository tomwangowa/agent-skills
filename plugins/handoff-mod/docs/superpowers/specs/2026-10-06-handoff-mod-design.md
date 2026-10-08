# Handoff Mod 設計

日期：2026-10-06  
狀態：**草案。** 待決項目 D1 至 D14 已於 2026-10-07 全部決定（D15、D16 於 2026-10-08 增補，見 [啟動清單展開與自動筆記折疊](2026-10-08-handoff-list-expand-design.md)），整份設計仍待 Tom 最後確認；標「未驗證」的行為 PoC 沒測到。2026-10-07 最後確認前的核對補了 6 點（Tom 選 A，彙整見文末「最後確認前的補充」）；同日 Cloud 補驗後再修訂（Tom 選 A，見文末「補驗後的修訂」），其中 3 項建議已由 Tom 全部採用，記為 D12 至 D14。  
plugin 暫名 `handoff-mod`，面板與提示的繁體中文文案暫定「接著做」。  
證據：[micro-PoC 結果](../../poc-results.md)（Cloud 與 Tom 本機實測：macOS、Warp、Claude Code 2.1.291 至 2.1.292）；驗證計畫：[micro-PoC 計畫](../plans/2026-10-06-handoff-mod-poc.md)。

## 目的與範圍

中斷工作後重開 session，多數人不知道怎麼交接；沒有自己 harness 的同事更是如此。本 plugin 做兩件事：

1. 在**會丟失狀態的時刻**（context 快滿、要 `/clear`）提示並協助寫交接檔。
2. 下次**啟動新 session** 時，列出「上次未完成、你可能想接」的項目，由使用者選擇接續。

這不是活動日誌（「最近幾天做了什麼」），不是稽核證據，也不跨機器同步。

**第一版包含：** 內建 skill、門檻觸發、`/clear` 攔截、啟動讀回、交接檔格式與新鮮度檢查、認領、結束筆記（D4）、使用計數（D5）。  
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
| 與 attention-mod 同載入（本機）：寬視窗並排不遮蔽，band 收到的 `viewport` 是扣掉右側面板後的寬度（72 欄時 `bodyColumns=67`）；窄視窗 attention-mod 切成 inline，band 被擠到 `↓2 more` 之後看不到 | 寬視窗用 band，按鈕列要在 67 欄內放得下；窄視窗改用 `$.ui.status` 常駐一行＋指令（D9） |
| attention-mod 的「外部輸入」會列出 `$.ui.log` 的通知（本機） | 正式 mod 的 `$.ui.log` 要克制，只留對使用者有意義的訊息 |
| mod 自己開 pane：80 欄 `isPlaced:false`，170 欄 `true`（門檻 144 欄） | 不用 pane |
| `$.ui.ask` 彈出引擎的提問對話框，2–4 個選項，另附「Type something」與「Chat about this」，被關掉或 `-p` 時 reject。本機：對話框不能單獨按數字，要方向鍵加 Enter；使用者不回答不會卡住回合，對話框在 `turn.complete` 之後仍開著 | `/clear` 攔截用它；reject 一律視為取消；要處理過期的對話框 |
| `session.end`：本機 `/exit`、`Ctrl-C` 兩次、關分頁都會觸發（`reason` 分別是 `prompt_input_exit`、`prompt_input_exit`、`other`），hook 寫一行檔案 1–10 ms；`Ctrl-D` 在 Tom 的環境不是離開；`kill -9`、當機沒有 | 結束時留事實筆記技術上可行（D4） |
| `session.compact` 在壓縮開始前約 41 ms 觸發（`trigger:"manual"`），帶著 messages，可回 `{skip}` 否決；在這個 hook 裡能否 `$.ui.ask` 未驗證（本機） | T4 有機會，待驗 |
| `repo()` 回 `{root, remote, …}`，不在 git 內是 `null`；worktree 時 `repo().root` 是主 checkout，`session.root()` 是 worktree 自己；從 repo 子目錄啟動時 `session.root()` 就是子目錄，不會往上推（本機） | 範圍鍵見下；git repo 內以 `git rev-parse --show-toplevel` 為基準，不直接用 `session.root()`（D10） |
| `$.ui.ask` 的選項只有 `options`、`header`、`multiSelect`，沒有取消或中止（型別檔）。Cloud 補驗：Esc → reject（`no answer …`）；對話框開著時打字再 Enter，文字**不會送出**、沒有回合，Enter 選到預設的第一項 | mod 無法關掉已彈出的對話框；`$.ui.ask` 的使用規則與選項順序見 T2 |
| `$.command.register` 的指令名只允許字母、數字、`_`、`-`，最多 64 字元（型別檔、文件） | mod 註冊的指令不能叫 `handoff-mod:…`；啟動清單的指令用 `/handoff-resume` |
| `$.ui.status(text)` 每個 plugin 只有一行，`undefined` 清除，最多 2000 字（型別檔）。Cloud 補驗：80、100 欄、attention-mod inline 面板開著時，畫在輸入框**下方**單獨一行，格式 `⚠ <plugin>: <text>`；`$.ui.toast` 也有畫出（位置未逐幀確認） | 窄視窗降級的常駐一行可用（D9）；是警告外觀，文案要短、不用嚇人的字（見補充 6） |
| `register(on, options)` 收到 manifest 的 `userConfig` 值（依宣告的型別，預設值已補）；`/config` 畫成 `<plugin>.<field>` 一列（`options` 的字串欄位是選單）；`$.config.set` 有檢查 `min`／`max`，超出回 `{deny}`（Cloud 補驗） | 正式設定走 `userConfig`（元件 9） |
| **改 `userConfig`（`$.config.set` 或 `/config`）會重載整個模組**：`session.start` 再觸發一次、計時器停掉、module 變數歸零，新值立刻生效（Cloud 補驗） | module 變數不能存要保留的狀態；啟動時的初始化要可重複執行；見元件 2 的狀態規則 |
| `$.state` 的值在模組重載後保留，`/clear` 後重置（Cloud 補驗：計數器 2 → 重載後 2 → `/clear` 後 0；需 manifest `types` 與 `types/index.d.ts` 宣告，`atom`／`read`／`update` 從 `claude-code` 匯入） | 「這個 session 別再問」等 session 範圍的狀態放 `$.state` |
| `$.prompt.fill` 可以在 `command.run` hook 內直接呼叫，回 `{isFilled:true}`（Cloud 補驗） | `/handoff-resume <編號>` 不需要經計時器 |
| 指令回傳的 `{text}` 與 `context` Claude 讀得到；`$.ui.log` Claude 讀不到（Cloud 補驗：標記字串，Claude 只答得出前兩者） | 指令輸出選哪一個，見元件 3 |
| `$.store` 的檔案：目錄 `0700`、檔案 `0600`、明文 JSON（Cloud／Linux 補驗；macOS 未驗） | D4 備案的 store 副本見元件 8 |

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
| T1 門檻 | `percent` 有值且 ≥ 門檻（預設已用 60%，D1）；`turn.complete` 之後閒置、沒有等待；有未完成跡象；本 session 沒被抑制；這個門檻沒問過 | band，三個按鈕；窄視窗且有 attention-mod 時改 `$.ui.status` 常駐一行＋指令（D9） |
| T2 `/clear` | 互動 session；`turns() > 0`（D3：不看未完成跡象，一律詢問） | `$.ui.ask`，三個選項 |
| T3 手動 | 使用者自己下 `/handoff-mod:handoff` | 無，skill 直接執行 |
| T4 壓縮前 | **日後，第一版不含。** `session.compact` 在壓縮前觸發且可否決，但 hook 內 `$.ui.ask` 未驗證 | 無 |

**未完成跡象**（假設，未驗證）：本 session 有成功的 `Edit`／`Write`／`NotebookEdit`，或 `git status` 不乾淨。純問答的 session 不需要交接，沒有這個條件使用者會一直被問。這個條件用在 T1 與結束筆記；T2 依 D3 不看它。

**T1 的三個選項：**

| 鍵 | 動作 |
| --- | --- |
| 1 同意 | 開始交接（見下） |
| 2 再多 10% 再問 | 隱藏 band；下一個門檻 = 目前 % ＋ 10 個百分點 |
| 3 這個 session 別再問 | 這個 session 不再提示；存在 `$.state`（模組重載後保留，`/clear` 後重置，語意正好相符；module 變數會在使用者改任何設定時歸零，**不可用**）。**已決（D12）。** |

不操作等於暫緩：band 保持顯示，不重複彈出；`/clear`、新 session 時消失。

**門檻狀態會重置：** `percent` 在壓縮與 `/clear` 後會下降（本機：9% → 5%），所以「下一個門檻」與「這個門檻沒問過」要在 `session.compact`、`/clear`（新 session id）時清掉；或在 `percent` 低於上次問過的值時重新起算。否則舊的下一個門檻會讓提示在一大段區間都不出現。

**哪裡存這些狀態（D12，Tom 已決）：** 「下一個門檻」「這個門檻問過沒有」「別再問」「有一個提問在等」這類 session 範圍的狀態放 `$.state`，不放 module 變數。原因：改設定會重載模組（Cloud 補驗），module 變數會被歸零；`$.state` 在重載後保留、在 `/clear`／`/resume`／`/branch` 後重置，和上面「`/clear` 時要清掉」的需求一致。`/clear` 不會重載模組，所以 module 變數也不會自己清掉，若有留在 module 的狀態，要在 `classic.SessionStart`（`source` 為 `clear`）明確重置。代價：`$.state` 要在 manifest 宣告 `types` 與型別檔；尚未在實作層面比較過用 `$.store`（以 session id 為鍵）的做法。

**T2 的三個選項與順序（D13，Tom 已決）：** 取消／先交接再清除／直接清除。**預設標在第一項**（Cloud 補驗：直接按 Enter 一定選到第一項，對話框開著時打字不會被當成新提示、也不會送出），所以第一項要是「按錯也無害」的選項：把「取消」放第一，使用者必須明確選才會開始交接或清除。原本的順序（先交接再清除／直接清除／取消）會讓意外的 Enter 開始一個交接回合。選「先交接」時 hook **不呼叫 `next`**，回 `{text}` 說明「已暫停清除，交接完成後請再下 `/clear`」，並從計時器開始交接。「直接清除」呼叫 `next(e)`；取消、關閉、reject 都回 `{text}` 不執行。`-p` 或非互動時不攔截。

**`$.ui.ask` 的使用規則（避免過期對話框）：** `AskOptions` 沒有取消或中止的欄位（型別檔），mod 無法自己關掉一個已經彈出的對話框；L4 也量到回合結束後對話框仍開著。所以第一版：

1. `$.ui.ask` **只**在 T2 的 `/clear` hook 內呼叫，並且 `await`，這時 `/clear` 被擋在 hook 裡，對話框不會比它的指令活得更久。
2. **不從計時器或其他事件呼叫** `$.ui.ask`（T1 一律用 band 或 `$.ui.status`）。
3. 用旗標避免疊加：已有一個提問在等時，不再發第二個。
4. 回答若在 session 重置（epoch 改變）之後才到，丟棄，不執行任何動作。

使用者在提問開著時直接輸入新提示會怎樣，**沒有驗證**，列入實作前風險。

**同意之後：** 從計時器呼叫 `$.command.run({command})`。`command` 是 `handoff-mod:handoff`，或在 D7 選用且偵測到時為使用者自己的 `handoff`。

**不信任「已寫好」：** 之後的 `turn.complete`，mod 掃描交接目錄找 mtime 晚於開始時間的新檔並解析 frontmatter；成功才 toast 顯示路徑；否則顯示「未偵測到有效交接檔」。

### 3. 啟動讀回

- **時機：** `classic.SessionStart`，`source` 為 `startup` 或 `clear`（`resume`、`fork`、`compact` 不顯示，對話已有脈絡）；互動 session；`turns() == 0`。
- **來源：** 目前 worktree（`git rev-parse --show-toplevel`）的交接目錄；`repo().root` 不同時再加上主 checkout 的目錄；同 repo 其他 worktree 的目錄用 `git worktree list` 取得（D2 已決），不另做索引；非 git 目錄只看自己的 `root()`。
- **排序：** 同 `root` 優先，其次同 `repo`，其餘依 `created` 由新到舊。預設展開 3 筆，其餘折疊成「還有 N 筆」按鈕，按下去（或 `/handoff-resume all`）展開（D16）。創建超過 14 天的預設折疊；同 `root` 加 `branch` 的較舊自動筆記也折疊，只有最新一份有資格進前 3 筆（D15）。
- **每筆顯示：** 任務（≤80 字）、branch、多久以前、新鮮度事實、「下一步」第一行（≤120 字）。
- **按鈕：** 接續、略過。「略過」只對這個 session 有效，不改狀態。
- **介面：** 寬視窗用 band，與 attention-mod 並排時把自己的內容與 `next(e)` 的結果並排（L8 已驗證可並排，按鈕列要在 67 欄內放得下）。**窄視窗且有 attention-mod 時 band 看不到**（L8：被擠成 `↓2 more`），啟動清單與 T1 一樣降級（D9）：`$.ui.status` 常駐一行「有 N 筆未完成交接，輸入 `/handoff-resume` 查看」，加上 `/handoff-resume` 指令。
  - `/handoff-resume`（無參數）：列出清單與編號；`/handoff-resume <編號>`：等同按「接續」（填入輸入框、認領）。寬視窗也可使用，不只限於降級。
  - 指令名不能含冒號（`$.command.register` 只允許字母、數字、`_`、`-`，型別檔與文件），所以不是 `/handoff-mod:…`；`handoff-mod:handoff` 是 plugin skill，命名空間由 plugin 提供，不是這個規則的例外。
  - **`$.ui.status` 每個 plugin 只有一行**（型別檔：`undefined` 清除）。啟動清單的那行在使用者送出第一個提示時移除（`turns() > 0`）；T1 的那行之後才可能出現，兩者不會同時存在。
  - **清單輸出（D14，Tom 已決，用 `$.ui.log`）：** Cloud 補驗：`{text}` 與 `context` 的內容 Claude 讀得到，`$.ui.log` 讀不到。清單只是給使用者看，Claude 不需要讀到；用 `$.ui.log` 就不會讓檔案裡的文字（任務、下一步）在使用者選擇之前進入 context，也不花 token。代價：attention-mod 的「外部輸入」會列出這些行（L8），所以行數與內容要克制。
  - `prompt.fill` 可以在 `command.run` hook 內直接呼叫（Cloud 補驗），所以 `/handoff-resume <編號>` 不需要經計時器。
- **接續：** `$.prompt.fill({text})`，文字是「請先讀 `<路徑>`，驗證其中前提是否仍成立，再接續『下一步』」。只放路徑，不放整份內容。使用者按 Enter 才送出。

### 4. 交接檔格式（schema 1）

位置與檔名：`<base>/.claude/handoffs/<branch 淨化>--<YYYYMMDD-HHMMSS>.md`（`base` 見範圍鍵）（沒有 git 時 branch 用 `no-branch`）。

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
source: auto                # 只有結束筆記（D4）有；省略表示使用者確認過的交接
---

## 任務
## 已完成
## 未完成
## 下一步
## 前提（人工確認）
## 規矩（不能違反）
## 已驗證／未驗證（AI 自述）
```

**讀取規則：** 章節標題中文與英文都認（`## 下一步` 與 `## Next` 等，D11）；只要求 `status` 與 `created`；其餘缺了就不顯示該項；不認得的欄位忽略。為了相容 Tom 現有的 `handoff`，`worktree` 視為 `root` 的別名；`assertions` 第一版忽略。

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

**交接檔位置（D2、D10 已決）：** 放 `<base>/.claude/handoffs/`（git repo 內 `base` 是 toplevel），在 git repo 內檢查是否已被忽略，沒有就寫進 `$(git rev-parse --git-path info/exclude)`，避免弄髒同事的 `git status`。

### 8. 結束筆記（D4，自動寫入，未經使用者審查）

`session.end` 時自動寫一份只含事實的筆記，不呼叫模型。放同一個交接目錄，檔名 `<branch 淨化>--<時間>--auto.md`，frontmatter `source: auto`。

**寫入條件：** 互動 session；`turns() > 0`；有未完成跡象（定義見 T1）；`reason` 不是 `clear`（`/clear` 由 T2 處理）。其他一律不寫。

**內容：** `task` 用最後一個使用者要求（截斷）；本文只有「最後一個要求」「最後一段回應」「branch／HEAD」「有改動的檔案清單」。不寫工具輸出，不寫更早的對話。

**緩解措施（Tom 已確認，2026-10-07；預設開啟）：** 因為沒有「先看過再寫」的關卡、又含對話原文，所以：

1. 目錄已被 `.git/info/exclude` 擋掉（D2），檔案權限 `0600`。
2. 兩段原文各截斷到 2000 字，去除控制字元與 ANSI 碼。
3. 寫入前套一道祕密樣式遮蔽（金鑰、token、`Authorization`、`password=` 之類），規則明列並單元測試。這是減少風險，不是保證；仍可能漏掉。
4. 啟動讀回時標「自動留下，未經審查」，超過 7 天不顯示；`HANDOFF_AUTO_NOTE=off` 可整個關掉。
5. 在 `session.end` 的共用預算（約 1.5 秒）內做完，逾時就放棄，不留半個檔案。

**未驗證：** `$.session.messages()` 能不能在 `session.end` 內讀。headless 量到的結果是**讀不到**（`no session is bound in this process`），互動 session 沒測；`git status` 約 76 ms、寫檔加 `chmod 600` 約 16 ms（headless），預算不是問題。**備案（也未驗證）：** 不在結束時讀訊息，改成平時記：在 `prompt.submit` hook 記下最後一個使用者要求、在 `turn.complete` 記下最後一段回應（事件的 `text`），存在 `$.store`，結束時只負責寫檔。實作前要先在互動 session 驗證其中一條可行，否則 D4 做不出來。

**備案的額外措施（Tom 選 A，2026-10-07；上面五條只管最後寫出的檔案，不管 `$.store` 裡的副本）：**

1. 寫進 `$.store` **之前**就先套用緩解措施 2 與 3（各截斷到 2000 字、去除控制字元與 ANSI 碼、祕密樣式遮蔽）；store 裡不放未遮蔽的原文。
2. 每個 session 只留一組（key 含 session id，每回合覆寫，不累積歷史）；結束筆記寫完就刪除；session 重置（`/clear`、新 session id）時刪除舊的。
3. `kill -9` 或當機會留下殘餘，所以每次啟動時清掉超過 7 天的 key（與緩解措施 4 的「超過 7 天不顯示」一致）。
4. **`$.store` 檔案的權限：Cloud（Linux）已驗證**，目錄 `~/.claude/plugins/store/` 為 `0700`、檔案為 `0600`，內容是**明文 JSON**（所以第 1 點的遮蔽仍然必要）。**macOS 未驗證**，實作前請 Tom 在本機看一次（`ls -l ~/.claude/plugins/store/`）；若不是 `0600`，要在 mod 能做到的範圍內處理，做不到就在文件寫明殘餘風險，並考慮備案是否仍值得做。store 檔在 key 超過 `cleanupPeriodDays` 沒被讀寫時由引擎清除，不等同「結束筆記寫完就刪」，兩者都要。

### 9. 設定

正式的設定走 plugin 的 `userConfig`，不要求使用者設環境變數：型別檔說明 `register(on, options)` 會收到 manifest 宣告的 `userConfig` 欄位值（已補預設值），存在 `settings.json` 的 `pluginConfigs`，並且在 `/config` 畫成 `<plugin>.<field>` 的一列（有 `options` 的字串欄位畫成選單）。同事用 `/config` 就能改。

| 欄位 | 預設 | 對應的測試覆寫（環境變數，只給測試與開發用） |
| --- | --- | --- |
| 門檻（已用 %）（D1） | `60` | `HANDOFF_THRESHOLD_PCT`（測試設 `10`） |
| 介面語言（D8、D11） | `zh-TW`（另有 `en`） | `HANDOFF_LANG` |
| 結束筆記（D4） | 開 | `HANDOFF_AUTO_NOTE=off` 關閉 |

優先順序：環境變數 > `userConfig` > 預設。D1、D4、D11 決定的是預設值與行為，這裡只改「設定從哪裡來」。

**manifest 宣告（Cloud 補驗，`claude plugin validate --strict` 通過）：**

```json
"userConfig": {
  "thresholdPct": { "type": "number", "title": "…", "description": "…", "default": 60, "min": 1, "max": 99 },
  "lang":         { "type": "string", "title": "…", "description": "…", "options": ["zh-TW", "en"], "default": "zh-TW" },
  "autoNote":     { "type": "boolean", "title": "…", "description": "…", "default": true }
}
```

- `title` 與 `description` 必填；`options` 讓 `/config` 畫成選單；`min`／`max` 由引擎檢查，超出時 `$.config.set` 回 `{deny}`。
- 值存在 `settings.json` 的 `pluginConfigs`；`--plugin-dir` 載入時鍵是 `<name>@inline`。
- **改任何一個設定都會重載模組**（`session.start` 再觸發、計時器停止、module 變數歸零）。後果：啟動時的初始化（例如清 7 天前的殘餘）必須可重複執行；進行中的計時器與 `await` 會被中斷；session 範圍的狀態放 `$.state`（元件 2）。
- 測試覆寫仍用環境變數；以 `$.env.get` 在使用時讀取，不在重載後才生效的位置快取。

## 資料流

```text
turn.complete / session.measure ─▶ usage ─▶ decideTrigger ─▶ band（1／2／3）
/clear ─▶ command.run hook ─▶ ui.ask ─▶ 先交接（不 next）｜直接清除（next）｜取消
同意 ─▶ clock.after ─▶ $.command.run(handoff) ─▶ 一個回合 ─▶ turn.complete ─▶ 驗證新檔 ─▶ toast
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

## 決定紀錄（D1 至 D14）

| 編號 | 問題 | 決定（或我的傾向） |
| --- | --- | --- |
| D1 | 門檻的語意與預設值。你的原意是「剩餘低於 40%」（原文寫成 60%，是筆誤），等於已用 60%；在 1M window 是 60 萬 token，在 200k 模型約 12 萬 | **已決（Tom，2026-10-07）：** 預設已用 60%，純百分比、可設定，不加絕對 token 上限（L1：`percent` 與 `/context` 一致，可用）。測試階段用環境變數 `HANDOFF_THRESHOLD_PCT` 覆寫，測試時設 `10`（1M window 下新 session 約 4%，10% 約十萬 token，不會一開始就達標）；其他觸發條件不因測試而繞過 |
| D2 | 交接檔放 repo 內 `.claude/handoffs/`（跟著 worktree、刪 repo 就沒了）還是使用者目錄（不污染 repo、換機不跟）；跨 worktree 看不看得到 | **已決（Tom，2026-10-07）：** repo 內 `<toplevel>/.claude/handoffs/`，加 `.git/info/exclude`；啟動讀回時用 `git worktree list` 把同 repo 其他 worktree 的交接列在下面並標來源；不做使用者目錄、不另做索引（L2：skill 寫進該 worktree 自己的目錄） |
| D3 | `/clear` 在沒有未完成跡象時也要問嗎？取消 `/clear` 的做法（不呼叫 `next`）你能接受嗎？ | **已決（Tom，2026-10-07）：一律都問**（與我的傾向「沒跡象就放行」不同）；取消做法隨選項接受，文案要清楚。後果：純問答的 session 也會在 `/clear` 時被問一次 |
| D4 | 結束時用 `session.end` 自動留一份只含事實的接續筆記（最後一個要求原文、最後一段話原文、branch、有改動的檔案），不呼叫模型 | **已決（Tom，2026-10-07）：做，含對話原文。** 設計見元件 8；五條緩解措施已確認，預設開啟（`HANDOFF_AUTO_NOTE=off` 關閉）。L6：`/exit`、`Ctrl-C` 兩次、關分頁都觸發 `session.end`（`kill -9`、當機沒有）。**未驗證：** `session.end` 內能否讀 `$.session.messages()`、在約 1.5 秒預算內讀完並寫入 |
| D5 | 要不要記錄「交接寫了幾次、最後接續了幾次」來判斷有沒有價值？這需要持久化 | **已決（Tom，2026-10-07）：** 要，只放 `$.store`，本機計數，不外傳 |
| D6 | plugin 與 skill 的名稱（暫 `handoff-mod`、`handoff-mod:handoff`） | **已決（Tom，2026-10-07，最後確認前核對選項 A）：** `handoff-mod`、`handoff-mod:handoff`，另有指令 `/handoff-resume`（見元件 3） |
| D7 | 偵測到使用者自己的 `handoff` 時，優先用它還是一律用內建？ | **已決（Tom，2026-10-07）：一律用內建。** 你自己的 skill 格式只有 Tom 一個人保證相容。L2：你的 `handoff` 能由 `$.command.run` 啟動、Review Gate 與寫檔都成立，但不觸發 `skill.prompt`，且曾把沒跑過的指令標成已驗證 |
| D8 | 同事是否都讀繁體中文？介面字串要不要預留抽出 | **已決（Tom，2026-10-07）：** 繁體中文加英文，兩種都做。選語言與交接檔標題的處理見 D11 |
| D9 | 窄視窗且有 attention-mod 時，band 被擠出可見範圍（L8），門檻提示怎麼辦 | **已決（Tom，2026-10-07）：** 窄視窗用 `$.ui.status` 常駐一行＋指令（`/handoff-mod:handoff`），直到交接完成或選「不再問」才拆掉；寬視窗用 band。`$.ui.status` 與 `$.ui.toast` 只有型別檔說明，PoC 沒實測，實作前要先驗證在 attention-mod inline 模式下看得到 |
| D10 | 交接目錄的基準：git repo 內用 `git rev-parse --show-toplevel`（每個 worktree 一份），還是 `session.root()`（從子目錄啟動會各有一份，L7）？ | **已決（Tom，2026-10-07）：** git repo 內用 toplevel；不在 git 內才用 `root()`；啟動目錄記在檔案的 `root` 欄當標籤 |
| D11 | 雙語帶來的兩個問題：(1) 介面語言怎麼選（`$.env` 變數、Claude Code 的語言設定，是否可讀沒查證）；(2) 交接檔的章節標題（`## 任務`、`## 下一步`…）是中文，啟動讀回靠標題找「下一步」，英文版標題怎麼辦 | **已決（Tom，2026-10-07）：** 解析器同時認中英標題，檔案語言由使用者語言決定；介面語言先用環境變數 `HANDOFF_LANG`（預設 `zh-TW`），自動偵測等查證可行再加。本機查過：`settings.language` 未設、`LANG=C.UTF-8`，沒有可靠的自動偵測來源，語言以 `HANDOFF_LANG` 為準 |
| D12 | session 範圍的狀態（下一個門檻、別再問、有提問在等）放哪裡？改設定會重載模組、歸零 module 變數 | **已決（Tom，2026-10-07）：放 `$.state`**，不放 module 變數。Cloud 補驗（W10）：重載後保留、`/clear` 後重置。代價：manifest 要宣告 `types` 並附型別檔。沒有拿 `$.store`（以 session id 為鍵）做過比較 |
| D13 | T2（`/clear` 攔截）的選項順序；預設標在第一項，Enter 一定選到它（W8） | **已決（Tom，2026-10-07）：取消／先交接再清除／直接清除**，取消放第一。代價：想直接清除的人要多按一下方向鍵 |
| D14 | `/handoff-resume` 的清單輸出用哪種方式 | **已決（Tom，2026-10-07）：用 `$.ui.log`**，不用 `{text}`。Claude 讀不到，檔案內容在使用者選擇前不進 context、不花 token；代價：attention-mod 的外部輸入會列出這些行，所以行數與內容要克制 |
| D15 | 同 `root` 加 `branch` 的較舊自動筆記是否折疊、折疊到哪 | **已決（Tom，2026-10-08）：折疊，不隱藏。** 每個 branch 只有最新一份自動筆記有資格進前 3 筆，較舊的進「還有 N 筆」（算進 N、展開後看得到並標示）；手動交接不分組；程式無法判斷是否同一任務，所以不做任務判斷。詳見 [啟動清單展開與自動筆記折疊](2026-10-08-handoff-list-expand-design.md) |
| D16 | 折疊項目何時建立資料 | **已決（Tom，2026-10-08）：展開時才建。** 「還有 N 筆」按鈕與 `/handoff-resume all` 把 `$.state` 的 `expanded` 設為 true 再重建；啟動時只替前 3 筆跑 git 新鮮度。`/handoff-resume <n>` 超出範圍時先展開再找 |

## 驗證與測試

- **純函式用 `claude plugin test` 單元測：** `decideTrigger`、frontmatter 解析、排序、新鮮度事實的格式化、文字淨化。先寫會失敗的測試。測試不呼叫模型、不跑 git（git 以注入函式替代）。
- **事件接線由實機驗證：** attention-mod 的經驗是測試 kit 無法端到端觸發部分事件，接線只能靠程式碼審查與實機。哪些事件在 `handoff-mod` 的測試 kit 可觸發，**沒有查證**。
- **實機劇本：** 門檻提示三個選項各走一次；`/clear` 三條路；兩個終端機同時接續同一份；worktree；非 git 目錄；有交接檔與沒有交接檔的啟動；交接回合沒寫出檔案。
- 交接內容的準確度要用真實 session 人工抽查，不在自動測試範圍。
- **PoC 沒測到的（Tom 於 2026-10-07 決定停止補測，列為實作前風險）：** `/cd` 之後的 `root()`、`session.compact` hook 內的 `$.ui.ask`、自動壓縮的 `trigger` 值、`$.ui.status` 與 `$.ui.toast` 的實際顯示、Warp 以外的終端機、同事的環境（版本、managed settings）。
- **最後確認前核對新增的項目，Cloud 已補驗（2026-10-07，見 poc-results.md「補驗」）：** `userConfig`（宣告、型別、`/config`、`min`／`max`、改值後重載）、`$.state` 在重載後保留與 `/clear` 後重置、`prompt.fill` 在 hook 內可用、`{text}`／`context`／`$.ui.log` 的可見性、`$.store` 檔案權限（Linux）、T2 四條路徑、`$.ui.status`／`toast` 與 attention-mod inline。
- **仍待 Tom 本機：** macOS 的 `$.store` 檔案權限；T2 的行為在 Tom 的環境（`$.ui.ask` 不能單獨按數字，Cloud 沒有比對）。

## 不做的事

活動日誌或「最近做了什麼」、跨機器同步、稽核用途的證據保證、不經使用者確認就寫檔（D4 除外，已決）、由 mod 修改交接檔、`model.fork` 起草交接（日後可選）、`/compact` 攔截（T4，日後；`session.compact` 內的 `$.ui.ask` 未驗證）、跨 agent、檔案內 `assertions` 的自動檢查。

## 最後確認前的補充（2026-10-07，Tom 選 A）

最後確認前讀完整份設計後發現的 6 處缺口或矛盾，Tom 選擇全部照提議修改。D1 至 D11 已決定的內容沒有動。

| # | 問題 | 改了什麼 | 位置 |
| --- | --- | --- | --- |
| 1 | D4 備案把對話原文存進 `$.store`，緩解措施沒管這份副本 | 寫入 store 前先截斷與遮蔽；每 session 一組、寫完即刪、啟動清 7 天前殘餘；store 檔權限列為實作前驗證 | 元件 8 |
| 2 | 窄視窗＋attention-mod 時，啟動清單同樣被擠出（D9 只管 T1） | 啟動清單同樣降級為 `$.ui.status` 一行；新增 `/handoff-resume` 指令。提議時寫的 `/handoff-mod:resume` 不合法（指令名不能含冒號），改為 `/handoff-resume` | 元件 3 |
| 3 | T4 在觸發點表寫「有機會」，「不做的事」卻寫「待 L5」 | T4 明確為「日後，第一版不含」，兩處一致 | 元件 2、不做的事 |
| 4 | 設定全靠環境變數，同事不會設 | 正式設定走 `userConfig`（`/config` 可改），環境變數只當測試覆寫；欄位行為未實測 | 元件 9 |
| 5 | `$.ui.ask` 過期對話框沒有規則 | 提議時寫的「視為取消」不可行：`AskOptions` 沒有取消機制。改為只在 `/clear` hook 內 `await`、不從計時器呼叫、不疊加、重置後的回答丟棄 | 元件 2 的 T2 |
| 6 | `$.ui.status` 會帶 `⚠` 與 mod 名稱，常駐一行像警告 | 文案要短、不用嚇人的字；一個 plugin 只有一行，啟動清單與 T1 不同時出現 | 已查證表、元件 3 |

D6（名稱）在這次一併記為已決。

## 補驗後的修訂（2026-10-07，Cloud 補驗，Tom 選 A）

Cloud 補驗（`poc-results.md` 的 W1 至 W10）後對設計做的修訂。D1 至 D11 已決定的內容沒有動。前 3 項原為我的建議，Tom 已於 2026-10-07 全部採用，記為 D12 至 D14。

| # | 內容 | 狀態 | 位置 |
| --- | --- | --- | --- |
| 1 | session 範圍的狀態（下一個門檻、別再問、有提問在等）放 `$.state`，不放 module 變數：改設定會重載模組、歸零 module 變數；`$.state` 重載後保留、`/clear` 後重置 | **已決（D12，Tom 採用）** | 元件 2 |
| 2 | T2 的選項順序改成「取消／先交接再清除／直接清除」，因為 Enter 一定選到預設的第一項、打字不會送出 | **已決（D13，Tom 採用）** | 元件 2（T2） |
| 3 | `/handoff-resume` 的清單輸出用 `$.ui.log`（Claude 讀不到），不用 `{text}`（Claude 讀得到） | **已決（D14，Tom 採用）** | 元件 3 |
| 4 | `$.store` 檔案權限：Linux 為 `0700`／`0600`、明文；macOS 待 Tom 本機驗證 | 已改（事實） | 元件 8 |
| 5 | `userConfig` 的宣告、型別、`/config`、`min`／`max` 已驗證；改設定會重載模組，啟動初始化要可重複執行 | 已改（事實） | 元件 9、已查證表 |
| 6 | `prompt.fill` 可在 `command.run` hook 內直接呼叫，`/handoff-resume <編號>` 不需要計時器 | 已改（事實） | 元件 3 |
| 7 | `$.ui.status`、`$.ui.toast` 在 attention-mod inline 面板開著時可見（status 在輸入框下方一行） | 已改（事實） | 已查證表 |

## 來源

- [Use the mods API](https://code.claude.com/docs/en/plugins/mods/api)、[Mods reference](https://code.claude.com/docs/en/plugins/mods/reference)、[Draw in the interface](https://code.claude.com/docs/en/plugins/mods/interface)、[React to events](https://code.claude.com/docs/en/plugins/mods/events)。
- 本機型別（Claude Code 2.1.291 產生，已 gitignore）優先於公開文件。
- 既有設計慣例：[Attention Mod 設計](../../../../attention-mod/docs/superpowers/specs/2026-10-03-attention-mod-design.md)。
