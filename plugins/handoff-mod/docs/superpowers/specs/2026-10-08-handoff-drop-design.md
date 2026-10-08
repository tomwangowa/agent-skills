# 放棄交接與「本 session 忽略」

日期：2026-10-08  
狀態：**草案，待 Tom 審閱。** 這份是 [handoff-mod 設計](2026-10-06-handoff-mod-design.md) 元件 3「啟動讀回」與 [啟動清單展開與自動筆記折疊](2026-10-08-handoff-list-expand-design.md) 的增補，新增決定 D17、D18；D1 至 D16 已決定的內容沒有動。

## 起因

作者在 macOS 實測 0.1.2 時按了清單底下的「略過」，開新 session 後同樣的交接又原封不動地跳出來。這是設計本來的行為（設計主檔元件 3：「略過」只對這個 session 有效，不改狀態），程式也是這樣寫：按鈕只把 `$.state` 的 `listDone` 設成 true 並收起清單。

但它暴露了兩個缺口：

1. **沒有任何按鈕或指令能讓一份交接「不再出現」。** 一份交接要離開清單，只有三條路：按「接續」（標成 resumed）、超過 7 天的自動筆記自動隱藏、超過 14 天被折進「還有 N 筆」（只是折疊，仍計入標頭的 N）。一份不打算接續的手動交接，會永遠留在清單裡。
2. **「略過」兩個字容易被理解成「別再提醒我」**，跟實際行為差很遠。

## 範圍

**做：**

- 新增 `/handoff-resume drop <編號>` 與 `/handoff-resume drop all`，把交接標成放棄（D17）。
- 按鈕「略過」改名為「本 session 忽略」，行為不變（D18）。
- `/handoff-resume`（無參數、`all`）的輸出最後多一行提示，指令說明文字也提到 `drop`。

**不做：**

- **不做復原指令。** `abandoned` 只能手動刪 `$.store` 裡 `state:<path>` 的紀錄才能撿回來；交接檔仍在磁碟上，要看可以直接讀。這是作者的決定。
- 不在 band 加按鈕。band 已經很擠，而且「全部放棄」不該離手指太近。
- 不記放棄的次數（D5 的統計只有寫了幾次、接續幾次）。
- 不做「延後 N 天再提醒」。
- 不改 7 天隱藏、14 天折疊、`SHOWN = 3`，也不改 D15 的折疊規則。
- 不改交接檔（不變條件 6：寫完就不再修改）。

## 決定

### D17：放棄的出口

用指令 `/handoff-resume drop <編號>` 與 `/handoff-resume drop all` 把交接標成放棄。

- **寫法與接續同一種：** 在 `$.store` 寫 `state:<path>` = `{status: 'abandoned', at, sessionId}`。`effectiveStatus` 本來就讀這個覆寫，而 `abandoned` 不在 `OPEN_STATUSES`（`hooks/handoff-file.js`），所以清單會自動排除，`rank.js` 不用改。
- **編號：** 跟 `/handoff-resume <編號>` 用同一套編號。編號超出目前顯示範圍但落在總數內時，先展開再找（D16）。
- **`drop all`：** 放棄清單裡的全部，含折疊的。必須打完整的單字 `all`，不接受縮寫或空參數。
- **三道保險（因為 `$.ui.ask` 只能在 `/clear` hook 裡用，不變條件 3，沒辦法跳出確認，又不做復原）：** 必須是完整的 `all`；執行後用 `$.ui.log` 逐筆列出放棄了哪些（標題加 branch）；被別的 session 正在接續的不動。
- **別的 session 正在接續（`claimed`）的不放棄：** `drop all` 跳過這些並說明；`drop <編號>` 打到這種會回「另一個 session 正在接續，沒有放棄」。認領的 12 小時 TTL 內有人正在處理，不該被另一個 session 清掉。
- **放棄後重建清單。** 因為編號會往前遞補，輸出會寫明「剩下的編號已重排」。全部放棄、清單空了，band 與狀態列隨之消失。
- **只有目前看得到的才能放棄。** 超過 7 天的自動筆記本來就不顯示（D4），所以也不能放棄；它們不會出現在清單，也就不會干擾。

被否決的做法：

- 只改文案、不加出口：缺口還在，8/18 那種舊交接永遠留著。
- 延後 N 天再提醒：要多存時間戳，行為也比較難向使用者說明。
- 在 band 上加「放棄」按鈕：band 已經很擠，且「全部放棄」不該那麼容易按到。
- `drop` 只支援單筆：清單堆很多時要打很多次。
- 不支援 `all`：同上。有 `all` 的風險由三道保險控制。
- 提供復原指令：作者決定不做。

### D18：「略過」改名為「本 session 忽略」

按鈕文字 `list.skip` 改成「本 session 忽略」（英文 `Ignore for this session`）。行為不變，仍然只是把 `listDone` 設為 true 並收起清單，不改任何狀態。

理由：原名讓人以為「別再提醒我」，實際上新 session 會重新出現。

## 設計

### 1. `hooks/i18n.js`

中英兩份必須有相同的 key 與占位符（既有測試會擋）。

| key | zh-TW | en |
| --- | --- | --- |
| `list.skip`（修改） | `本 session 忽略` | `Ignore for this session` |
| `cmd.resume`（修改） | `列出未完成的交接；/handoff-resume <編號> 接續其中一筆；drop <編號\|all> 放棄` | `List unfinished handoffs; "/handoff-resume <n>" resumes one; "drop <n\|all>" abandons` |
| `list.dropHint`（新增） | `不要的可以放棄：/handoff-resume drop <編號\|all>` | `Not needed? Abandon them: /handoff-resume drop <n\|all>` |
| `cmd.resume.hint`（修改） | `[編號\|all\|drop]` | `[n\|all\|drop]` |
| `drop.usage`（新增） | `用法：/handoff-resume drop <編號\|all>` | `Usage: /handoff-resume drop <n\|all>` |
| `drop.header`（新增） | `已放棄 {count} 筆，剩下的編號已重排：` | `Abandoned {count}; the remaining items are renumbered:` |
| `drop.claimed`（新增） | `另一個 session 正在接續，沒有放棄：{title}` | `Another session is resuming this, not abandoned: {title}` |
| `drop.none`（新增） | `沒有可以放棄的交接。` | `Nothing to abandon.` |

`list.bad` 沿用（`drop` 的編號無效時）。

### 2. `hooks/register.js`

`/handoff-resume` 的 handler 把參數拆成第一個字與其餘：

| 輸入 | 行為 |
| --- | --- |
| `drop`（沒有第二個字，或第二個字既不是整數也不是 `all`） | 記 `drop.usage`，不動任何東西 |
| `drop <n>` | 必要時先展開（同 `<n>`）；找到且沒被認領就放棄；找不到記 `list.bad`；被認領記 `drop.claimed` |
| `drop all` | 設 `expanded`、重建；對每一筆沒被認領的放棄；被認領的各記一行 `drop.claimed`；一筆都沒放棄記 `drop.none` |
| 其他 | 同 0.1.2 |

放棄一筆的函式（`abandon`）只做：`$.store.set('state:<id>', {status: 'abandoned', at: now, sessionId})`，回傳成功與否。寫入失敗的視為沒放棄，不出現在輸出的清單裡（標頭的筆數只算成功的），其餘照常；整體仍 fail-open（不變條件 2）。

放棄完成後 `refreshList($, {force: true})`，再用 `$.ui.log` 輸出 `drop.header` 與逐筆的放棄標題（沿用 `item.title`，編號是放棄前的）。

無參數與 `all` 的輸出，在 `list.moreCmd` 那一行（若有）之後固定多一行 `list.dropHint`；清單為空時不顯示。

### 3. 按鈕

`ui.render` 裡 key 為 `skip` 的按鈕，標籤用新的 `list.skip`，其他不變。

## 錯誤處理

- store 寫入拋錯：該筆視為沒放棄、不出現在輸出裡，其餘照常；標頭的筆數只算成功的。
- 重建清單失敗：沿用 `refreshList` 內部的 `catch`，輸出已經寫完，不重複。
- `drop` 的編號是整數但落在範圍外（0、負數、超過總數）：`list.bad`；不是整數（文字、小數）或沒給編號：`drop.usage`。兩者都不動任何東西。
- `drop all` 時清單是空的：`list.none`（同現有）。

## 測試

`tests/register.test.ts`：

- `drop <n>` 寫入 `state:<path>` 的 `abandoned`，清單重建後少一筆，輸出列出該筆與「編號已重排」。
- `drop <n>` 超出顯示範圍但在總數內：先展開再放棄。
- `drop <n>` 打到被別的 session 認領的那筆：不寫入、輸出 `drop.claimed`。
- `drop all`：全部（含折疊的）都寫入；被認領的跳過並各有一行說明；清單空了之後 band 與狀態列清掉。
- `drop all` 但每一筆都被認領：輸出 `drop.none`，不寫入。
- `drop`、`drop abc`、`drop 1.5`：不寫入，輸出 `drop.usage`；`drop 0`、`drop -1`、`drop 99`：不寫入，輸出 `list.bad`。
- 放棄後的交接，換一個 session 重新啟動也不再出現。
- 無參數與 `all` 的輸出最後一行是 `list.dropHint`（有折疊時在 `list.moreCmd` 之後）；清單為空時沒有。
- 按鈕 `skip` 的標籤是新文字，按下去仍只收起清單、不寫 `state:`。

**要更新的既有測試：** 現有測試用 `w.rec.logs.length` 檢查輸出行數（`twoHandoffs` 的無參數輸出 3 行、`fiveHandoffs` 的 5 行、`all` 的 8 行），以及 `logs[4]` 是 `list.moreCmd`。多一行提示後都要加 1，`moreCmd` 的位置不變，提示行在最後。

`tests/i18n.test.ts`：既有的「key 相同」「占位符相同」兩個測試會擋新 key。

完成後照專案慣例做變異檢查：弄壞一處、確認有測試變紅、還原。建議的變異點：拿掉 `claimed` 判斷、把 `abandoned` 寫成 `resumed`、`drop all` 不展開。

## 文件與版號

- 設計主檔：決定紀錄表補 D17、D18；元件 3 的「按鈕」一行改成「接續、本 session 忽略」並提到 `drop`。
- README（繁中、英文）：補 `drop` 的用法，以及「本 session 忽略」只對這個 session 有效。
- `types/index.d.ts`：沒有新的 `$.state` atom，不用動。
- 版號：升 0.1.3（改了 hook 行為；版號沒變時 `plugin update` 不會拉新程式碼，這是專案已記的教訓）。

## 已知限制

- 放棄沒有任何復原指令，只能手動刪 `$.store` 的 `state:<path>` 紀錄。
- 放棄只存在這台機器的 `$.store`，不跟交接檔走：同一份交接在另一台機器上仍然是未完成。
- 超過 7 天的自動筆記不顯示，所以不能放棄；它們本來就不會出現在清單裡。
- `drop all` 沒有二次確認（`$.ui.ask` 的限制），安全靠完整單字加逐筆輸出，輸出之後無法反悔。
