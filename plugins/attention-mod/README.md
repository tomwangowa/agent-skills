# 你到底在忙什麼

Claude Code Attention Mod 的本機原型。回到目前工作階段時，面板顯示目標、Claude 的工作脈絡、正在執行的工具、最近證據與待回答訊號。

## 安裝

需要 Claude Code 2.1.288 以上。在終端機執行：

```sh
claude plugin marketplace add tomwangowa/agent-skills
claude plugin install attention-mod@tomwangowa --scope user
```

裝好之後，新開的 session 都會載入這個 Mod。不想用時可以停用或移除：

```sh
claude plugin disable attention-mod@tomwangowa
claude plugin uninstall attention-mod@tomwangowa
```

要更新到新版本，執行 `claude plugin update attention-mod@tomwangowa`，重新啟動 Claude Code 後生效。

Mod 不在 sandbox 裡執行，會以你的使用者權限跑在 Claude Code 裡，安裝前請先看過 `hooks/` 的程式碼。

## 開發時載入

不安裝、只在這次 session 載入：

```sh
claude --plugin-dir "<這個資料夾的路徑>"
```

如果已經安裝過，開發時請先停用已安裝的版本，不然同一個 session 會有兩個面板。

## 開啟

面板預設開啟，不搶輸入焦點；若啟動時未放置，輸入 `/attention`。寬終端機的原生全螢幕模式使用側邊面板，窄終端機則放在輸入框上方。標題後面的「收起面板」按鈕會縮小面板，做法依放置方式而不同：

- **放在輸入框上方（inline）**：面板收成兩行，第一行是標題與「展開面板」，第二行是單行狀態；再按一次展開。收起的狀態在 `/clear`、`/resume` 後保留，重載外掛才回到展開。
- **側邊面板（dock）**：面板高度由 Claude Code 決定，外掛縮不了，所以按「收起面板」會關掉面板，並在輸入框下方留一行狀態（`動作：…（輸入 /attention 展開）`，前面由 Claude Code 自動加上 `attention-mod:`）；輸入 `/attention` 才會重新打開。

狀態那一行平常顯示「動作」，有問題或權限在等你時改顯示「需要你」，所以收起後也不會漏掉。要完全關掉面板，用原生的 ×；關掉後更新不會重新打開，`/attention` 可重開，不送出主 Claude 的新工作提示。

側邊面板（dock）用三個圓角框分區：摘要是藍色，外部輸入是洋紅，「即時」框依狀態變色——有工具在跑是綠色，有東西等你是黃色，閒置時用終端機預設色。放在輸入框上方時（inline）維持原本的版面，欄位名稱上色，「動作」「需要你」前面多了狀態點 ●，底部的附註變淡。顏色用終端機的具名色，會跟著你的終端機主題走。

## 回饋

面板底部的「回饋」按鈕可回報使用問題或改善建議。輸入內容（可用 `bug:` 或 `idea:` 開頭分類）後按 Enter，面板會產生一條 Teams 連結；點開後 Teams 會開啟與收件人的聊天並預填好訊息，確認後在 Teams 按 Enter 才會送出。也可以按「複製內容」取得純文字，自行貼到其他地方。

### 設定收件人

回饋要傳給誰，由外掛設定 `feedbackRecipient` 決定，值是收件人的 Teams 登入 email。為了不把任何地址放進公開 repo，程式碼沒有預設值，**每位使用者安裝後都要自己填一次**；請向維護者 tom_wang 索取收件人的 Teams 登入 email。

兩種設定方式：

1. 安裝時的設定畫面，或之後輸入 `/config`，找到「回饋收件人」欄位修改（Mod 會用新值重新載入）。
2. 直接編輯 `~/.claude/settings.json`（`you@example.com` 換成收件人的地址）：

   ```json
   {
     "pluginConfigs": {
       "attention-mod": {
         "options": { "feedbackRecipient": "you@example.com" }
       }
     }
   }
   ```

   用 `--plugin-dir` 載入時，key 是 `attention-mod`（或 `attention-mod@inline`）；從 marketplace 安裝時的 key 可能是 `attention-mod@tomwangowa`，還沒實機確認，請以 `/config` 實際寫入的內容為準。

沒設定時，按下面板的「回饋」會在表單裡顯示設定步驟（輸入 `/config`、填「回饋收件人」、儲存），並只提供「複製內容」；填了但不是單一合法 email 時，開頭改成「目前的值不是單一合法 email，請重新設定」，其餘相同。兩種情況都可以先輸入內容，複製出來的文字和傳給收件人的訊息相同（含 `[attention-mod …]` 標籤）。收件人要和你在同一個 Teams 租戶，才找得到對方。

- Mod 本身不送出任何網路請求，也不寫檔、不存 store；是否送出由你在 Teams 決定。
- 連結只含你輸入的文字和分類標籤，不附帶對話、路徑、工具內容或 session 資訊。
- 連結長度上限約 2,000 字元（編碼後），中文一字佔 9 字元。收件人 email 約 25 字元時，單行輸入大約 200 個中文字或 1,800 個英文字母；email 越長可用的越少。超過會截斷連結內的文字並提示，「複製內容」永遠是完整文字。
- 草稿只在記憶體，重載、`/clear`、`/resume` 或結束 session 後清空。

## 資訊怎麼來

「動作」「需要你」來自原生事件。「目標」「脈絡」「證據」由獨立的 `haiku` 呼叫整理既有對話與工具節錄，摘要保留來源識別。資料只存在 Mod 記憶體，不使用 store、不另讀工作區檔案。Claude Code 本身仍依其設定保存原本的對話。

「外部輸入」列出最近 3 筆不是你打、但進了 Claude context 或顯示在對話裡的內容，例如 hook 注入、附件、工具帶進來的內容；背景工作回報、排程或其他 session 送進來的訊息會不會列出，還沒實機確認。notice 也會列出，不過它只顯示在畫面上，model 不會讀到。附時間、種類、來源，最新 2 筆另外附單行節錄。它只顯示，不會成為摘要素材；資料只在記憶體，`/clear`、resume、重載後清空。已知的系統附件（token 提醒、環境、工具清單等）由 `hooks/inputs.js` 的黑名單濾掉，沒見過的種類照樣顯示。事後追查請看對話紀錄 JSONL，每一列都有時間。

有新素材才呼叫模型，開始時間至少相隔 60 秒，同時最多一個；素材含 JSON 和省略標記最多 8,000 個 Unicode 字元，回應最多 512 tokens，15 秒逾時。模型呼叫會使用你的 Claude 用量，實際金額或方案消耗沒有固定估計值。

回應接受原文 JSON，或完整、單一的 JSON code block；只移除完整外框，夾帶說明仍拒絕。脈絡引用須來自 Claude 發言，證據引用須來自工具結果，不能引用工具參數或使用者要求當作結果。

模型失敗或回應不符合格式時，保留原摘要及其時間，顯示「摘要更新失敗」。來源引用存在不代表內容已經驗證；假設仍須保留假設語氣。工具成功、回合結束或一段時間沒有事件，都不表示任務完成。

「目前沒有待回覆訊號」表示未觀測到等待。權限路由 `ask` 只能顯示「等待狀態不明」；確實畫出主工作問題介面，才顯示等你回答。權限通知在無法對應單一活動時也降級為未知。

新提示使舊摘要失效，執行中的工具仍繼續追蹤。clear／resume 切換使舊資料失效；在途模型呼叫仍持有鎖，較晚到達的舊回應不回填新任務。clear／resume 後若沒有重啟事件，會等待原生工作階段識別改變再恢復摘要。重載會重建目前對話，不繼承等待訊號。恢復素材的時間是本次讀取時間，不能拿來當原訊息的發生時間。

## 驗證

```sh
claude plugin validate --strict .
claude plugin test .
```

原生測試包含有界素材、來源與格式驗證、並行工具、慢模型、失敗、重設、節流、面板與本機指令；不會真的呼叫模型或執行 Bash。

[原型結果與尚未驗證項目](docs/prototype-results.md)、[設計](docs/superpowers/specs/2026-10-03-attention-mod-design.md)、[本機 API 契約](docs/runtime-api.md)。
