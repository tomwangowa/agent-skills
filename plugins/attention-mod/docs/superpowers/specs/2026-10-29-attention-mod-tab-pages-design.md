# 面板三頁：即時、次要、Quick Notes

日期：2026-10-29  
狀態：已實作，目標版本 0.6.0，實機手動檢查（第 9 項）尚未完成。Tom 於 2026-10-29 逐節確認（第 1 至 6 節）。

## 問題

- 面板目前所有內容擠在一頁，18 列放不下。模型、額度、已載入 skill、MCP 伺服器這類資訊佔版面，但不需要一直看。
- 工作中常想記一些臨時文字，目前只能另外開記事本。這些文字要跨啟動保留，並且依專案分開。

## 決定

### 三頁內容

- **即時**：摘要、即時、外部輸入、子代理（子代理是即時狀態，留在這頁）。
- **次要**：工作樹、模型、努力程度、額度、已載入 skill 與 MCP 伺服器數量、回饋表單（移到頁底）。
- **Quick Notes**：一個多行輸入框。
- 現有面板沒有身分列。設計裡也不新增身分列；探針畫面的 identity 只用於測試。

### 切頁

- 三顆按鈕，文字是「即時」「次要」「Quick Notes」，hotkey 分別是 `1`、`2`、`3`，目前頁會標示。
- `/attention` 不切頁，只開面板或展開。
- `/attention 1`、`/attention 2`、`/attention 3` 切頁並開面板。其他參數只開面板，頁碼不變。
- 指令描述改為「開啟工作脈絡面板；/attention 1–3 切頁」。

### 頁碼規則

- 頁碼存在記憶體，規則與現有的 `collapsed` 相同：跨 `/clear` 與 resume 保留，只有插件 reload 才重設回第 1 頁。
- 收合時不畫頁面內容；展開後回到原來的頁。

### Quick Notes 的存放

- 儲存位置是 `$.store`，這是插件自己的 key-value 空間，跨 session 與熱重載保留。
- key：有 git 時用 `notes:<git 共用目錄>`；不在 git 裡時用 `notes-cwd:<目錄>`。同一個 repo 的所有 worktree 共用一份筆記。
- value：字串，就是筆記文字。
- 上限：每份 32,768 個 code point。超過就不存，顯示「未存：超過上限」。`$.store` 是整個插件共用的空間，超過 4 MiB 會拒絕寫入，所以要有單份上限。
- 文字清空時呼叫 `$.store.delete`，不留空的紀錄。
- 目前沒有刪除單份筆記的介面，只能清空文字。

### Quick Notes 的讀取與存檔

- **四種狀態：**
  - 讀取中：目錄還沒對上，或 `$.store.get` 還沒回。不掛載輸入框，只顯示「讀取中」。
  - 就緒：掛載輸入框，文字一律來自記憶體中的 `notes.text`，不直接讀存檔。
  - 讀取失敗：顯示「讀取失敗」與「重試」按鈕。這個狀態不存檔。
  - 存檔失敗：文字留在記憶體，顯示「未存」，每 5 秒重試一次。
- **讀不到就不寫。** 讀取失敗時不寫入，避免空白內容把已存的筆記蓋掉。
- **存檔時機：**
  - 每次編輯更新 `notes.text`、記下最後編輯時間，並標記未存。
  - 沿用現有的 1 秒計時器：有未存內容，且距最後編輯超過 1 秒，就寫入。實際延遲在 1 到 2 秒之間，因為計時器每秒才檢查一次。
  - Enter 立刻存。
  - 同一時間只跑一次寫入。寫入中又有編輯，下一次檢查再寫。
  - 切頁不等存檔完成。文字在記憶體中，回到第 3 頁時仍顯示同一份內容。
- **編輯中切換目錄：** 先把舊 key 的未存內容寫入舊 key，再切到新 key 的讀取流程，輸入框換成「讀取中」。文字留在開始打字的那個 repo。
- **不跟 session 重設。** 筆記只跟目錄與 key 有關，`/clear` 不清空筆記。
- **焦點：** Quick Notes 的輸入框不設 `autoFocus`。按 3 切到這一頁後，焦點不會自動跳進筆記，後續的數字鍵仍能切頁。回饋表單的 `autoFocus` 一併拿掉。

### 次要頁的資料來源（全部唯讀）

- 模型：`$.session.model()`。
- 額度：`$.session.usage()` 回傳的 `rateLimits`，取 `five_hour` 與 `seven_day`。
- 已載入 skill 與 MCP 伺服器數量：`$.session.usage({breakdown:'summary'})`。只用 `summary`，因為它在本地估算、不送請求。`full` 會對每個工具與記憶檔送 token 計數請求，本設計禁止使用。
- 努力程度：`turn.step` hook 讀取 effort。型別顯示 effort 可能是字串，也可能是數字，兩種都要處理。讀不到顯示「未知」。
- 工作樹：沿用現有讀取，但要保留共用目錄（見「元件與資料流」）。

### 版面與焦點

- **inline 版面**（`rows: 18`）：header 之下先放頁籤按鈕，再畫該頁內容。
- **dock 版面**：每一頁畫成有框的區塊。收起（park）時留下的狀態列只看事件與等待狀態，和頁碼無關。
- 版號：`0.5.2` 改為 `0.6.0`，`hooks/meta.js` 與 `.claude-plugin/plugin.json` 一起改。

## 為什麼這樣決定

- **用 `$.store`，不用檔案。** 跨啟動保留的需求只有插件自己的存檔空間能滿足。檔案寫入被不變條件禁止，而且要自己處理路徑與權限。
- **用 git 共用目錄當 key，不用 cwd。** 這個專案常用 worktree，同一個專案在不同 worktree 會有不同 cwd，cwd 當 key 會把筆記切散。代價是要保留一個新欄位，而且 key 依賴讀取時序（見「錯誤處理與不變條件」）。
- **讀不到就不寫。** 寫入空白內容會直接蓋掉舊筆記，是最難復原的失敗。
- **頁碼規則與 `collapsed` 相同。** 使用者用 × 關掉面板、再用 `/attention` 打開，頁碼不應該被重設。

## 方案

- **方案 A（cwd 當 key，1 秒自動存）：** 最簡單，但同一專案的 worktree 各自一份筆記。使用者在主 checkout 寫的內容，在功能 worktree 看不到，容易被當成資料遺失。未採用。
- **方案 B（git 共用目錄當 key，1 秒自動存）：** 採用。
- **方案 C（cwd 當 key，只在 Enter 與切頁時存）：** 沒有計時器，但離開 Claude Code 前沒按 Enter 的文字會遺失。未採用。

## 元件與資料流

- `hooks/worktree.js`：`parseWorktree` 多回傳 `commonDir` 欄位。指令本來就讀這個值，只是沒有保留。
- `hooks/notes.js`（新增，純函式）：管理 Quick Notes 狀態（key、status、text、dirty、lastEditAt、saveError），判斷「現在該不該存」，以及 key 切換時要先寫哪一個 key。不碰 `$`。
- `hooks/view.js`：新增三頁的版面組裝函式（純函式），延續現有做法。
- `hooks/register.js`：
  - 持有頁碼與筆記狀態；呼叫 `$.store.get`、`set`、`delete`。
  - 計時器在現有的 `clock.every(1000)` 裡多做一件事：檢查是否該存。
  - 新增 `turn.step` hook，讀 effort 後呼叫 `next(e)` 並原樣回傳。
  - `command.run` 讀 `e.args`（字串），解析頁碼。
- 讀取時序：工作樹與 key 只在 session 啟動、每回合開始、`/clear` 綁定新對話時更新。使用者 `cd` 後，計時器偵測到目錄改變，要觸發一次讀取。

## 錯誤處理與不變條件

- **工作樹讀取時序：** 讀取結果記下當時目錄。目錄與目前不同時，key 不能用，Quick Notes 顯示「讀取中」，不載入也不存檔。
- **存檔失敗：** 文字留在記憶體，顯示「未存」，每 5 秒重試。成功後清掉警告。
- **讀取失敗：** 顯示「讀取失敗」與「重試」按鈕，不存檔。
- **超過上限：** 不存，顯示「未存：超過上限」，文字留在記憶體。
- **插件失敗不影響主對話：** 所有 store 與 process 呼叫都包在 `try/catch` 裡，和現有觀察一樣。
- **不變條件草稿**（已由 Tom 確認，實作時才寫入 `plugins/attention-mod/.claude/CLAUDE.md`）：把「不用 store、檔案、http」改成：

  > 只用 clock、model.complete、session.id/messages/model/usage（唯讀，usage 只用 breakdown summary）、command.register、agent.list、session.cwd、turn.step（唯讀取 effort）、ui、store（只存 Quick Notes 文字）；process 只有唯讀的 git 讀取。不把提示、工具結果或摘要寫進 store、檔案或 http，也不提交主對話提示。

## 測試

- **純函式測試（先寫、先看失敗）：**
  - `notes`：讀取中、就緒、讀取失敗不存、1 秒門檻、Enter 立即存、同一時間只跑一次寫入、key 切換先寫舊 key、清空即刪、超過上限不存。
  - `worktree`：保留 `commonDir`；不在 git 時退回 cwd key。
  - 指令參數解析：`1`、`2`、`3` 切頁；其他值只開面板。
- **整合測試（`tests/fixtures.ts`）：**
  - 用 mock clock 推進時間，斷言實際的 `store.set` 次數與時機，不只看回傳值。
  - 用 `mounted.drawn()` 檢查三頁在 inline 與 dock 兩種版面。讀取中不出現輸入框，就緒後才出現。
- **三條回歸測試，先寫：** 讀不到就不寫；key 切換先寫舊 key；第一次讀取完成前不掛載輸入框。
- **手動檢查（沒有自動化，實測後才算已驗證）：** 見「尚未驗證」。
- **指令：** `claude plugin validate --strict .`（含 calls inventory）與 `claude plugin test .`。本機沒有 tsc，型別只能靠編輯器檢查，測試通過不代表型別編譯通過。

## 範圍外

- 多份筆記、搜尋、匯出、同步、刪除單份筆記的介面。
- 修改摘要的 prompt，或新增主對話提示。
- 註冊 attachment、hook-context、compaction、tool-message、note 這幾種 door。
- 身分列。
- `$.session.usage({breakdown:'full'})`。

## 同步要改的文件

- `plugins/attention-mod/.claude/CLAUDE.md`：不變條件（store 那條）與開發段落的版號說明。
- `plugins/attention-mod/docs/runtime-api.md`：新增 `$.store`、`$.session.model()`、`$.session.usage()`、`turn.step` 的使用。
- `plugins/attention-mod/README.md`：面板說明（實作後檢查是否需要更新）。
- `plugins/attention-mod/docs/decisions/2026-10-29-quick-notes-store.md`：決策紀錄，記錄為什麼用 store，以及為什麼用 git 共用目錄當 key。Tom 審閱本文件後才寫入。

## 技術可行性

已查證（本機型別檔 2.1.312）：

- `$.store`：插件自己的 key-value，跨 session 與熱重載保留；整個插件超過 4 MiB 會拒絕寫入。
- `$.session.model()`、`$.session.usage()` 存在；`usage` 的 `rateLimits` 與 `breakdown` 參數符合本設計。
- 輸入框：`rows` 可多行，Enter 送出，`autoFocus` 會取得焦點。
- 數字鍵 hotkey：只在插件面板持有焦點時生效。
- `clock.every(ms, fn)` 回傳取消函式。
- `command.run` 的 `e.args` 是字串。

已查證（探針與 Tom 的回報）：

- Quick Notes 用的 `$.store` 跨重啟保留。
- 數字鍵只在焦點在按鈕時生效。
- iTerm2 中 Shift+Enter 換行、Enter 送出（2026-10-29 截圖）。

## 尚未驗證（NOT VERIFIED）

- Enter 後輸入框畫面清空。截圖顯示清空，但內部變數仍有文字，型別檔沒寫這件事。實作時若清空，重繪時要把 `notes.text` 放回輸入框。
- 按鈕要怎麼用鍵盤進入輸入框。交接只寫了 Tab 移到按鈕、Esc 離開輸入框。
- 次要頁的回饋表單展開超過 18 列時，是否被裁切。
- `turn.step` 讀取 effort：實際會不會收到值，型別說可能是字串或數字，沒有實測。
- dock 的實際高度，以及三頁在 dock 中的表現。
- Warp 的數字鍵與 Shift+Enter 行為。
- iTerm2 中的貼上、Ctrl+J、Option+Enter，以及關閉 autoFocus 的版本（交接未完成項目）。

## 審稿時請確認

1. 子代理留在即時頁（交接沒有指定，這是假設）。
2. Quick Notes 上限 32,768 個 code point。
3. 頁碼規則採用 A（與 `collapsed` 相同）。
4. 回饋表單的 `autoFocus` 拿掉。
5. 版號 0.6.0。
6. 方案 B 採用，代價是多一段讀取時序與一個新欄位。
