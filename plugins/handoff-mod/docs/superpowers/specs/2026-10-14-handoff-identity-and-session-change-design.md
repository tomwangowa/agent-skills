# 交接的識別與「本 session 有變化」

日期：2026-10-14  
狀態：**草案，待 Tom 審閱。** 這份是 [handoff-mod 設計](2026-10-06-handoff-mod-design.md) 元件 3「啟動讀回」、元件 8「結束筆記」與 T1 門檻提示的修訂，新增決定 D20 至 D24；D1 至 D19 已決定的內容，除了下面明寫被取代的部分，都沒有動。目標版號 0.2.0。

## 起因

2026-10-14 作者在 `agent-skills` 開新 session，啟動清單顯示「有 26 筆未完成交接」，作者沒有寫過那麼多。用 `rank.js` 與 `register.js` 的邏輯重算，剛好 26 筆，來源是：

| 位置 | 計入 | 說明 |
| --- | --- | --- |
| `agent-skills-production/.claude/handoffs` | 10 | 2026-10-12 `~/.claude/skills` 改成 symlink 時，舊目錄的 11 份被複製過來（1 份檔案本身是 resumed） |
| `agent-skills/.claude/handoffs`（main） | 8 | 2026-10-08 從舊目錄帶過來的副本 |
| `.claude/worktrees/attention-handoff-mods-presentation-b88bb4` | 8 | 同一批副本 |

實際只有 11 份交接，原始檔在 `~/.claude/skills-legacy-20261012/.claude/handoffs/`。真正沒處理的只有 2 份。問題有三個：

1. **沒有去重。** `readHandoffs` 掃描每個 worktree，以絕對路徑當識別；內容相同、位置不同的副本被當成不同的交接。
2. **狀態綁死在路徑上。** 放棄與接續存在 `$.store` 的 `state:<絕對路徑>`。檔案換位置後對不上，8 份作者以前已經 abandoned 或 resumed 的交接全部變回未完成。
3. **自動筆記會重複寫。** `shouldWriteNote` 只看 `git status --porcelain` 有沒有輸出，untracked 也算；不比對上一份筆記，也不看這個 session 有沒有動過檔案（`trigger.js` 的 `editedFile` 沒有任何呼叫者傳入）。一個放著不管的 untracked 檔，會讓每個送過 prompt 的 session 結束時都寫一份筆記，內容是那個 session 跟變更無關的最後一問與回應。

這個 mod 已經對外（公司內）發佈，修正必須照顧已經有交接檔與 store 紀錄的使用者，而且升級的當下，還開著的 session 會繼續跑舊版，新開的 session 跑新版，兩者共用同一個 store。這是從 plugin cache 以版號分目錄推論出來的，沒有直接觀察過；作者機器上 0.1.0 至 0.1.5 的 `.in_use` 目前都是空的並標了 `.orphaned_at`，只能說明舊版現在已經沒有人在用。

## 範圍

**做：**

- 同一份交接的副本只算一筆（D20）。
- 狀態讀取時退回舊的 path key（D21），寫入時新舊 key 都寫（D22）。
- 結束筆記只在這個 session 造成變化時才寫（D23）。
- 60% 提示到門檻就問，不看 git 狀態（D24）。
- 順帶修正：筆記「有改動的檔案」的中文檔名不再是 git 的跳脫字串。

**不做：**

- 不清理磁碟上已累積的自動筆記（超過 7 天本來就隱藏）。
- 不處理「檔案已搬走、只剩舊路徑紀錄」的情況。
- 不用 `tool.call` 偵測編輯（看不到 Bash 裡的 `sed -i`；修改時間能涵蓋）。
- 不加設定項。`autoNote` 已經能整個關掉。
- 不改交接檔格式，也不改已寫好的交接檔（不變條件 6）。
- 停寫舊 key 的時間點不在這份決定；0.2.x 全系列都雙寫。

## 決定

### D20：交接的識別

**已決（Tom，2026-10-14）：檔名加 frontmatter 的 `created`。** key 是 `<檔名>|<created 的 ISO>`，例如 `main--20261009-111522.md|2026-10-09T03:15:22.000Z`；`created` 先經 `Date.parse` 正規化。

- 不改檔案格式，現有檔案直接適用，新舊版本寫的檔案可以互讀。
- 手動改內文不會讓狀態失效；改檔名會變成另一份。
- 唯一的誤判：兩個 worktree 在同一秒、用同一個 branch 名稱（例如都是 `no-branch`）各寫一份。接受。

被否決：內容 hash（手動改一個字狀態就失效）；frontmatter 加 `id`（舊檔沒有，仍要退回另一套規則）。

### D21：舊的 `state:<path>` 紀錄

**已決（Tom，2026-10-14）：讀取時退回。** 先查新 key，查不到就用每個副本現在的絕對路徑查 `state:<path>`。檔案仍在原位的舊紀錄全部保留；已經搬走的對不到，留在 store 不管。

被否決：啟動時一次遷移（多一段要可重複執行的程式、拖慢啟動）；不遷移（等於在其他專案重演一次 26 筆）。

### D22：相容程度

**已決（Tom，2026-10-14）：雙向相容。** 接續、放棄、claim 寫新 key，也替每個副本寫舊的 path key。升級後還開著的舊版 session 與降版都看得到新版的寫入。代價是每次寫入要寫 1 加副本數個 key；沒有副本的交接是 2 個。

被否決：只向後相容（新版放棄的，舊版 session 仍列出）；另加 store 格式版號（目前沒有用途）。

### D23：結束筆記的條件

**已決（Tom，2026-10-14）：這個 session 造成變化才寫。** 取代 D4 中「工作樹有未提交的變更」這一條。第一次送出 prompt 時記下 dirty 檔案的「狀態碼、路徑、修改時間」，結束時有新的路徑、修改時間變了、或檔案讀不到（被刪），才寫。

- 本來就在的 untracked 檔沒動過：不寫。
- 新建但還沒 `git add` 的檔案：寫。
- session 裡只做了 `git add`：狀態碼變了，寫。

被否決：不算 untracked（漏掉 Claude 新建的檔，改過的 tracked 檔仍每次重寫）；跟上一份自動筆記比對（第一個無關 session 仍會寫，又改一次同一個檔的真實工作反而被略過）。

### D24：60% 提示的條件

**已決（Tom，2026-10-14）：到門檻就問，不看 git 狀態。** 取代原設計「工作樹有未提交的變更才問」。乾淨的工作樹與非 git 目錄也會問。每個門檻只問一次、「這個 session 別再問」、交接進行中不問，這三項照舊。這是對外部使用者可見的行為改變。

## 設計

結構：新增兩個純函式模組，`register.js` 只負責接線，跟 `rank.js`、`trigger.js`、`note.js` 的寫法一致。

### 1. `hooks/identity.js`（新）

- `handoffKey(name, created)`：回傳 D20 的 key。
- `mergeCopies(found, {base, repo})`：依 key 分組。每組回傳 `{key, path, paths, meta, fields, fileClosed}`：`path` 是顯示與接續用的副本（在 `base` 下的優先，其次在 `repo` 下，其餘照掃描順序）；`meta` 與 `fields` 取自那一份；`fileClosed` 是任何一個副本檔案本身已處理。
- `stateKeys(item)`：`['state:id:<key>', 'state:<path1>', 'state:<path2>', …]`。`claimKeys(item)` 同理，前綴是 `claim:`。新 key 以 `id:` 開頭，舊 key 以 `/` 開頭，不會撞。

### 2. `hooks/snapshot.js`（新）

- `takeBaseline(entries)`：`entries` 是 `[{code, path, mtimeMs}]`，超過 50 筆只留前 50 筆並標 `truncated: true`。
- 刪除項目（狀態碼含 `D`）的檔案本來就不在磁碟上，記成 `mtimeMs: null`，不算 `stat` 失敗。
- `changedSince(baseline, current)`：以下任一成立回傳 `true`：`current` 中有 baseline 沒有的「狀態碼加路徑」；同一筆兩邊的 `mtimeMs` 不同；非刪除項目的 `mtimeMs` 是 `null`（讀不到）。同一筆兩邊都是 `null`（session 前就刪了、沒再動）算沒變化。

### 3. `hooks/handoff-file.js`

`parseHandoff` 現在遇到不在 `OPEN_STATUSES` 的狀態直接回 `ok: false`，已處理的副本因此不會出現在掃描結果裡，D20 的合併就無法得知「某個副本已處理」。改成：其他檢查都通過、只有狀態不是未完成時，仍回 `{ok: false, reason: 'status'}`，但多帶 `meta` 與 `fields`。

`ok` 的意思不變，所以只看 `ok` 的呼叫者不受影響，例如 `register.js` 檢查 skill 剛寫出的檔案是否有效的那段（約 467 行）：skill 寫出 `status: resumed` 的檔案仍算無效。只有 `readHandoffs` 把 `reason === 'status'` 且帶 `meta` 的結果標成 `closed: true` 放進結果，供合併使用。

### 4. `hooks/claim.js`

`tryClaim` 改收 `keys`：任何一個 key 處於他人佔用中（`claimView` 為 `other`）就不認領；否則每個 key 都寫，讀回第一個（新 key）驗證。store 失敗時照舊 `degraded`。

### 5. `hooks/register.js`

**啟動清單（`buildList`）：**

1. `readHandoffs` 之後 `mergeCopies`。
2. 狀態：依 `stateKeys` 查，有任何紀錄就取 `at` 最新的那筆的 `status`；都沒有時，`fileClosed` 為真就當已處理；否則用檔案的 `status`。
3. 被佔用：任何 `claimKeys` 是 `other`。
4. `rankHandoffs` 不改。清單項目的 `id` 改成 key；接續時填進輸入框的路徑用 `path`。

**寫入（`resume`、`abandon`）：** 對 `stateKeys` 全部寫 `{status, at, sessionId}`。成功與否看新 key；舊 key 失敗只記 trace。

**快照（`recordRequest`）：** `last:<sessionId>` 紀錄還沒有 `baseline` 時，執行 `git status --porcelain -z --untracked-files=all`，對每個非刪除路徑 `$.fs.stat`（git 根目錄加相對路徑），寫入 `baseline`；之後每次覆寫 request 都保留原有的 `baseline`。`git status` 失敗、任何一個非刪除路徑的 `stat` 失敗、或寫入失敗時不存 `baseline`。rename 與 copy 項目 `stat` 新路徑。

- `-z`：沒有 `-z` 時中文檔名被 git 轉成 `"\346\226\207.md"`，`stat` 找不到。
- `--untracked-files=all`：預設只顯示 `?? newdir/`，資料夾的修改時間不隨裡面的檔案改變。
- `-z` 的輸出以 NUL 分隔；rename 與 copy（狀態碼 `R`、`C`）後面多一個欄位是原路徑，解析時要跳過。路徑一律相對於 git 根目錄。
- `$.fs.stat` 在這個 mod 已有使用（檢查 skill 寫出的檔案，約 462 行），macOS 上可用。

**結束筆記（`writeEndNote`）：**

1. 用同一個 `git status` 指令取得目前清單；乾淨就不寫（跟現在一樣）。
2. 沒有 `baseline`、`truncated`、或比對沒在子期限 `min(500 ms, 剩餘預算的一半)` 內完成：照舊行為（dirty 就寫）。子期限從呼叫 `git status` 開始算，涵蓋 `git status` 與所有 `stat`。
3. 否則 `changedSince` 為真才寫，結果經 `hasUnfinishedSign` 傳給 `shouldWriteNote`。
4. 筆記的「有改動的檔案」改用 `-z` 的解析結果。

**門檻（`checkThreshold`）：** 拿掉 `git status` 與 dirty 條件，`hasUnfinishedSign` 固定為真。

### 新舊版本同時運作

| 情境 | 結果 |
| --- | --- |
| 新版放棄，舊版 session 重整清單 | 舊版查得到自己路徑的 `state:<path>`，藏起來 |
| 舊版放棄其中一個副本 | 新版退回查到那個舊 key，整筆藏起來；舊版自己仍列出其他副本（舊版原本的行為） |
| 新版寫入後降版 | 每個副本都有舊 key |
| 舊版 claim 一個副本，新版想接續 | 新版看到其中一個 claim key 被佔用，擋下 |
| 舊版建立的 `last:` 紀錄（沒有 `baseline`） | 結束時照舊行為 |

## 錯誤處理

一律 fail-open（不變條件 2）。

| 失敗 | 處理 |
| --- | --- |
| 快照時 `git status`、任何 `stat`、或 store 寫入失敗 | 不存 `baseline`，結束時照舊行為。不記部分快照，比對規則保持單純 |
| 結束比對逾子期限或丟例外 | 當成有變化，繼續寫（寧可多寫一份） |
| 寫筆記逾總預算 | 照現在：放棄，什麼都不寫 |
| 雙寫時部分舊 key 失敗 | 以新 key 為準，記 trace；舊版可能繼續列出那個副本 |
| 副本內文不同（手動改過其中一份） | 用顯示用副本的 `task`、`next`；其他副本只參與狀態判斷 |
| `created` 無法解析 | `parseHandoff` 本來就擋（`reason: 'created'`） |

## 測試

照 `.claude/CLAUDE.md`：每個純模組一個測試檔，接線用 `tests/world.ts` 的替身驅動。

- `tests/identity.test.ts`（新）：同一時間點不同寫法的 `created` 得到同一個 key；分組；顯示用路徑的優先順序；`fileClosed` 傳到整組；`stateKeys` 順序。
- `tests/snapshot.test.ts`（新）：沒變化；修改時間變了；新路徑；session 中被刪；session 前就刪了、沒再動（不算變化）；只有狀態碼變（`git add`）；rename；`truncated`。
- `tests/handoff-file.test.ts`：已處理的檔案回 `ok: false, reason: 'status'` 並帶 `meta`；skill 寫出 `status: resumed` 的檔案仍被寫入檢查判為無效。
- `tests/claim.test.ts`：多個 key 任一被佔用就擋；寫入每個 key。
- `tests/register.test.ts`：
  - 三個 worktree 有同一批副本，只列一筆（重現 26 筆）。
  - 預先放只有 `state:<path>` 的紀錄（模擬舊版），被採用。
  - `drop` 寫新 key 加所有舊 key。
  - 60% 提示在乾淨工作樹與非 git 目錄都會問。
  - 結束筆記：既有 untracked 沒動不寫；新 untracked 寫；修改時間變寫；無 `baseline` 照舊；子期限逾時寫；中文檔名正確。
- **會刻意改寫的既有測試**（行為依 D23／D24 改變，不是 regression）：
  - `register.test.ts` 的 `nothing is asked below the threshold, without a percentage, on a clean tree, or outside git` 與 `a clean working tree is not unfinished work`：拆出「乾淨工作樹、非 git 目錄也會問」。
  - `ending with unfinished work writes a facts-only note that the list can read back` 與 `no note when the tree is clean, when /clear ended the session, or when there was no request; ...`：前提改成「這個 session 造成變化」，替身要提供 `baseline` 與 `stat`。
- 變異檢查：每項接線改動至少弄壞一處，確認有測試變紅，再還原。

## 實作前 PoC（作者的 macOS）

| # | 要確認 | 做法 | 不如預期時 |
| --- | --- | --- | --- |
| 1 | 同一個 store 被並行寫入時不互相蓋掉 | 兩個 `--plugin-dir` session 載入同一個本機 plugin（共用 inline store），幾乎同時寫不同 key，確認都在 | 回頭改 D22 的寫入方式 |
| 2 | 結束時 `git status --untracked-files=all` 加 50 個 `stat` 在子期限內 | `HANDOFF_DEBUG=1`，在 untracked 檔案數量接近日常的 repo 上看 trace 的耗時，`git status` 與 `stat` 分開記 | 降低上限或回頭改 D23 |
| 3 | 快照比第一個工具呼叫早完成 | trace 記快照完成時間，比對第一回合寫出檔案的修改時間 | 快照改到 `session.start` |
| 4 | `/clear` 後 session id 是否改變 | `/clear` 前後各記 `$.session.id()` | 兩種結果都可接受，記錄即可 |

**結果（2026-10-14，詳見 [poc-results.md](../../poc-results.md) 的「0.2.0 實作前 PoC」）：**

1. 通過。兩個 session 各寫 300 個 key，store 檔裡兩組都完整；兩個還開著的 session 也都看得到對方的寫入。
2. 通過。`remainingMs` 約 1500；結束時 git 耗時 138 至 200 ms，`stat` 0 至 2 ms。耗時主要是啟動 git 的 process，跟 dirty 項目數關係不大（作者機器上最多 26 項的 repo，shell 直接量 102 至 122 ms）。沒有量到上百個 untracked 檔案的 repo。
3. **不通過，Tom 決定接受（選項 A）。** Claude Code 不等 `prompt.submit` hook 跑完就開始回合：hook 還在暫停時，第一個工具呼叫已經發生。原本以為「hook 能回傳 `drop`，所以引擎會等」，這個推論是錯的。實測 4 個 session，快照 123 至 234 ms 完成，第一個工具呼叫在送出後 2367 至 4168 ms，約 10 倍餘裕，所以快照仍在第一個 prompt 建立，競態列入已知限制。改到 `session.start` 也無法完全避免：`/clear` 之後的新 session 不會觸發 `session.start`（見 4）。
4. `/clear` 後 session id 會改變，而且新 session 不觸發這個 plugin 的 `session.start`。`classic.SessionStart` 在 `--plugin-dir` 下一筆都沒記到，原因未查明。

「不同版本共用同一個 store 檔」不另做 PoC：API 文件寫 store 是「this plugin's own key-value store, kept between sessions and hot reloads」，檔名 `handoff-mod_tomwangowa-5f441db4b8b2.json` 沒有版號，且 0.1.6 讀得到 0.1.6 之前寫入的 `state:` 紀錄。

## 文件與版號

- `plugin.json` 與 `package.json` 升到 0.2.0。
- README（中、英）：60% 提示到門檻就問（乾淨工作樹與非 git 目錄也會）；結束筆記只在這個 session 造成變化時才寫；副本只列一筆；刪掉「乾淨的工作樹（已全部 commit）與非 git 目錄不會被問」。
- release note：兩項可見的行為改變（D23、D24），以及「從 0.1.x 升級，以前放棄、接續過的狀態保留（檔案仍在原位時）」。
- 設計主檔：決定紀錄表補 D20 至 D24；D4 與 T1 條件那兩處加註「見 D23／D24」。

## 已知限制

- 檔案搬走後，舊紀錄對不到，那份交接會重新出現一次，要再 `drop` 一次。
- 兩個 worktree 同一秒、同 branch 名稱各寫一份交接時，會被當成同一份（D20）。
- 舊版 session 仍會分開列出副本，直到它結束。
- 純討論、沒動過檔案的 session，結束時不會留自動筆記，要自己執行 `/handoff-mod:handoff`。
- 快照和第一個回合同時進行（PoC 3）。模型的第一個工具呼叫如果比 `git status` 加 `stat` 還快（實測差約 10 倍，正常不會發生），那次改動會被算成「本來就有」，可能少寫一份筆記。
- `--untracked-files=all` 會把 untracked 資料夾展開成逐檔。一個超過 50 個檔案、又沒被 gitignore 的 untracked 資料夾，會讓快照每次都 `truncated`，那個 repo 就一直照舊行為（dirty 就寫）。
