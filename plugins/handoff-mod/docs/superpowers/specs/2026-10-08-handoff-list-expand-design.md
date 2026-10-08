# 啟動清單展開與自動筆記折疊

日期：2026-10-08  
狀態：**草案，待 Tom 審閱。** 這份是 [handoff-mod 設計](2026-10-06-handoff-mod-design.md) 元件 3「啟動讀回」的增補，新增決定 D15、D16；D1 至 D14 已決定的內容沒有動（含 D4：自動筆記預設開啟）。D15 在同日經 Tom 修正過一次：原本寫「被取代的完全隱藏」，改成「折疊但看得到」。

## 起因

作者在 macOS 實際使用時遇到兩件事：

1. 清單底下的「還有 2 筆」只是一行 dim 文字，沒有按鈕，`/handoff-resume` 也只列同一份前 3 筆，`/handoff-resume 4` 回「編號無效」。折疊的項目沒有任何辦法看到。
2. 每次 `/exit`、`Ctrl-C` 兩次都會寫一份自動筆記。條件只要求「這個 session 有跑過、`git status` 不乾淨」（`hooks/note.js` 的 `shouldWriteNote`），所以工作樹平常就有未 commit 檔案的 repo，每次離開都多一份，檔名帶時間戳，同一個 branch 越堆越多，啟動清單裡幾乎都是它們。

`autoNote` 開關早就存在（`/config` 的 `handoff-mod.autoNote`，測試用 `HANDOFF_AUTO_NOTE=off`），所以沒有再加開關。問題在於清單重複，不在於缺開關。

## 範圍

**做：**

- 「還有 N 筆」改成按鈕，按下去展開折疊的項目。
- `/handoff-resume all` 列出全部；`/handoff-resume <n>` 的 `n` 超出目前範圍時先展開再找。
- 同 `root` 加同 `branch` 的自動筆記，預設只展開最新一份；較舊的折進「還有 N 筆」，展開後看得到。

**不做：**

- 不改 `SHOWN = 3`、14 天折疊、7 天隱藏這三條既有規則（超過 7 天的自動筆記仍然不顯示）。
- 不改 `autoNote` 的預設值與寫入條件。
- 不刪、不改磁碟上任何交接檔（不變條件 6：寫完就不再修改）。
- 不嘗試判斷「是不是同一個任務」。自動筆記只有 `task`（最後一個要求的第一行）可參考，同任務的兩個 session 通常不同句，不同任務卻可能 branch、HEAD、有改動的檔案都一樣，任何判斷都會誤判。
- 不做「收合」按鈕；清單用「略過」整個拆掉。
- `/handoff-resume all` 的輸出不截斷行數。D14 要求克制，但這是使用者明確要求全部列出。

## 決定

### D15：同 branch 較舊的自動筆記預設折疊

同一個 `root` 加 `branch`（沒有 branch 時只用 `root`）的**自動筆記**，預設只有 `created` 最新的一份有資格進前 3 筆；其餘（「較舊的自動筆記」）一律折進「還有 N 筆」，展開或 `/handoff-resume all` 後看得到，並標示「同 branch 較舊的自動筆記」。

- **沒有任何一份消失。** 較舊的算進「有 N 筆」與「還有 N 筆」，只是預設不占前 3 個位置。
- 只有自動筆記分組。手動交接是人審過的，不進分組，也不會因為後來有自動筆記而被折疊。
- 在 `rank.js` 排序時計算，純函式；**不在 store 寫旗標**。檔案不動、沒有新狀態，輸入順序不影響結果（`created` 相同時以 `path` 決勝）。
- 順序在 7 天隱藏之後：先去掉超過 7 天的自動筆記（`hidden`，照舊不顯示），再對剩下的分組。
- 較舊的自動筆記不會因為前面的位置空出來而被補進 `shown`；要看就展開。

**修正紀錄（Tom，2026-10-08）：** 初稿寫「被取代的完全隱藏，也不算進 N」。Tom 指出同一個 branch 上可能做的是不同任務，舊的不能被蓋掉。程式無法分辨是否同一任務（見「範圍」），所以改成折疊而非隱藏。

被否決的做法：完全隱藏較舊的（會蓋掉不同任務的筆記，即上述修正）；只隱藏「branch、HEAD、最後一個要求都相同」的完全重複（幾乎抓不到東西）；新的手動交接也折疊舊自動筆記（多一條規則要維護）。

### D16：折疊項目何時建立資料

展開時才替折疊項目建立資料（含 `freshnessFacts` 的 git 呼叫），不在啟動時全部建好。

理由：交接檔一多，啟動時每筆都跑 git 會拖慢每個 session 的開頭，而這次要解決的問題正是檔案太多。代價是展開時要多跑一輪。

被否決的做法：啟動時全建（簡單，但有上述延遲）；只做指令不做按鈕（不符合需求）。

## 設計

### 1. `hooks/rank.js`

`rankHandoffs` 的回傳加兩個欄位：

| 欄位 | 內容 |
| --- | --- |
| `rest` | 排序後除了 `shown` 以外的其餘項目，順序同排序結果（含超過 14 天的、同 branch 較舊的自動筆記） |

`rest` 裡屬於 D15 的項目帶 `olderAuto: true`（回傳的是項目的複本，不改輸入），讓介面能標示。`shown`、`collapsed`（維持 `rest.length` 的意思）、`hidden` 不變；較舊的自動筆記算進 `collapsed`。

流程：開放狀態 → 去掉超過 7 天的自動筆記（`hidden`）→ 自動筆記依 `root` 加 `branch` 分組，每組最新一份以外標 `olderAuto` → 依分數與 `created` 排序 → 沒有 `olderAuto`、14 天內的前 3 筆為 `shown`，其餘為 `rest`。

### 2. `hooks/register.js`

- 新增 `$.state` atom `expanded`（預設 `false`）。不放 module 變數（不變條件 4）；`/clear` 後重置，重新開 session 也回到折疊。
- `buildList` 讀 `expanded`：`false` 只替 `shown` 建立 view；`true` 替 `shown` 加 `rest` 全部建立，編號連續。`total` 的算法不變（`shown.length + collapsed`）。
- band：`list.total > list.items.length` 時，原本的 dim 文字改成 `secondary` 按鈕（key `more`，不設 hotkey，延續既有「按鈕沒有 hotkey」的做法）。按下去：`expanded` 設為 `true`，再 `refreshList($, {force: true})`。展開後 `total == items.length`，按鈕自然消失。
- `refreshList` 已有 `listing` 鎖，連按兩下只有第一下生效；因為 `expanded` 在第一下就設好，重建時會讀到。
- 任何失敗照既有做法 fail-open，不影響主 session（不變條件 2）。

### 3. `/handoff-resume`

| 輸入 | 行為 |
| --- | --- |
| 無參數 | 列出目前清單；還有折疊時，最後多一行提示「還有 N 筆，輸入 /handoff-resume all 全部列出」（`$.ui.log`） |
| `all` | 設 `expanded`，重建清單，列出全部 |
| `<n>`，在範圍內 | 同現在：接續該筆 |
| `<n>`，超出範圍但 `total` 夠大 | 先展開再找；找到就接續 |
| 其他（非整數、超過 `total`） | 照舊回 `list.bad` |

`all` 在沒有折疊項目時等同無參數。

### 4. `hooks/i18n.js`

- `list.more`（現有，`還有 {count} 筆`）改當按鈕標籤使用，字串不變。
- 新增 `list.moreCmd`：`還有 {count} 筆，輸入 /handoff-resume all 全部列出`；英文 `{count} more. Run /handoff-resume all to list them all`。
- 新增 `list.older`：`同 branch 較舊的自動筆記`；英文 `Older automatic note on the same branch`。展開後，帶 `olderAuto` 的項目在 band 與 `/handoff-resume` 輸出各多這一行（dim）。
- 中英必須有相同的 key 與占位符（既有測試會擋）。

## 錯誤處理

- 展開時 git 失敗：`freshnessFacts` 本來就吃注入的 `git` 並回傳「無法驗證」，不會中斷建立清單。
- 展開時整個重建拋錯：`refreshList` 的 `catch` 吞掉，清單維持目前狀態，`expanded` 已是 `true`，下次重建會再試。
- 沒有折疊項目時按到 `all`：當成無參數，不回錯誤。

## 測試

`tests/rank.test.ts`：

- 同 branch 的兩份自動筆記，只有最新的可進 `shown`；較舊的在 `rest`、帶 `olderAuto`，且算進 `collapsed`。
- 前面位置空出來時，較舊的自動筆記也不會被補進 `shown`。
- 不同 branch、不同 `root` 的自動筆記互不折疊。
- 手動交接不帶 `olderAuto`，也不影響自動筆記的分組。
- 沒有 branch 時以 `root` 分組。
- 超過 7 天的自動筆記先算 `hidden`，不進分組、不算進 `collapsed`。
- `rest` 的內容與順序；輸入反序結果相同；輸入的項目物件沒有被改動。

`tests/register.test.ts`：

- 項目超過 3 筆時有 `more` 按鈕，且不是 dim 文字。
- 按下按鈕後全部列出，編號連續，按鈕消失。
- `/handoff-resume all` 列出全部；沒有折疊時等同無參數。
- `/handoff-resume 4` 自動展開並接續第 4 筆；超過 `total` 回 `list.bad`。
- 無參數且有折疊時，輸出多一行 `list.moreCmd`。
- 啟動時 `expanded` 為 `false`，只替前 3 筆跑 git（D16）。

完成後照專案慣例做變異檢查：弄壞一處、確認有測試變紅、還原。

## 文件與版號

- 設計文件主檔：決定紀錄表補 D15、D16，元件 3 的「排序」一行加上折疊規則與展開。
- README（繁中、英文）：補展開按鈕與 `/handoff-resume all` 各一句。
- 版號：目前的未 commit 改動已把 `plugin.json` 升到 0.1.1。這次改動併進 0.1.1 或升 0.1.2，等 commit 時問作者。

## 已知限制

- 折疊只看 `root` 加 `branch`，不判斷任務。同一個 branch 上做不同任務的自動筆記，舊的也會被折進「還有 N 筆」（看得到，沒有消失）。
- 「還有 N 筆」的 N 不會因為這次改動變小，只是前 3 個位置不再被同 branch 的舊自動筆記占掉。
- 超過 7 天的自動筆記仍然不顯示、也不能展開（D4 原本的規則，這次沒有動）；要看只能手動讀檔。
- 目前工作樹有尚未 commit 的邊框樣式改動（同一個 `ui.render` 區塊）。這次疊在上面做，commit 時再問要不要拆成兩個。
