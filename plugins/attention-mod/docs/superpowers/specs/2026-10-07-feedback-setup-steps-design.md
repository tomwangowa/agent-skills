# 回饋表單：沒設定收件人時顯示設定步驟

日期：2026-10-07  
狀態：Tom 於 2026-10-07 確認；目標版本 0.4.2。

## 問題

`feedbackRecipient` 沒設定時，按「回饋」只看到一行「尚未設定回饋收件人」，不知道去哪裡設定、要填誰。填了不合法的值（例如漏掉網域）也顯示同一行，使用者會以為設定沒存進去。

## 決定

- 收件人地址不進 repo。README 和面板只寫「維護者 tom_wang」，範例用 `you@example.com`。`2026-10-07-feedback.md` 的「repo 不含任何地址」維持不變。
- 沒設定或填錯時，表單照常打開，只是把那行警告換成設定步驟。設定前仍可輸入並「複製內容」。
- 面板不能替使用者寫設定（不用檔案、store、http），所以只顯示說明文字。
- 沒設定與填錯分開提示。
- 版號升到 0.4.2（改了 hooks 行為，見 lesson `bump-plugin-version-on-hooks-change`）。

## 畫面文字

沒設定：

```
尚未設定回饋收件人，設定步驟：
1. 輸入 /config，找到「回饋收件人」
2. 填收件人的 Teams 登入 email（向維護者 tom_wang 索取）
3. 儲存後面板會自動重載
設定前也可以直接輸入，用「複製內容」自行傳送。
```

填錯（有填但不是單一合法 email）：第一行改成「目前的值不是單一合法 email，請重新設定，步驟：」，其餘相同。設定正常時畫面不變。

## 元件

- `hooks/feedback.js`：新增 `recipientStatus(value)`，回傳 `'ok' | 'unset' | 'invalid'`（空值與全空白為 `unset`，`parseRecipient` 回 null 的非空值為 `invalid`），並匯出步驟文字常數。`parseRecipient` 不動。
- `hooks/register.js`：`register()` 同時存 `recipient` 與狀態；`drawFeedback` 依狀態畫對應的行。
- `README.md`「設定收件人」原節：維護者改成 tom_wang；第一種方式寫出欄位名稱「回饋收件人」；補一段說明沒設定與填錯時面板的行為。
- `plugin.json`、`hooks/meta.js`、`tests/view.test.ts`、`tests/integration.test.ts` 的標題字串：升到 0.4.2。
- `docs/decisions/2026-10-07-feedback.md` 補修訂紀錄；`.claude/CLAUDE.md` 的 `feedback.js` 條目補 `recipientStatus`。

## 測試

- `recipientStatus` 單元測試：空值、全空白、合法、非法、超過長度上限。
- 整合測試：沒設定時顯示步驟與 tom_wang；非法值顯示「不是單一合法 email」且不含「尚未設定」（取代 `tests/integration.test.ts` 現有的「非法收件人視同未設定」斷言）；設定正常時不顯示任何步驟。

## 不做

不改 `parseRecipient` 的規則，不新增設定項，不寫任何完整地址，不動 `docs/` 下其他歷史文件。

## 未驗證

- 步驟加警告共約 5 行（48 欄會折行），在 18 列的面板裡可能把「取消回饋」擠出畫面。測試只看得到元件樹，要安裝 0.4.2 後實機確認。
- `/config` 內的欄位名稱與說明已由 Tom 的截圖確認（2026-10-07）。
