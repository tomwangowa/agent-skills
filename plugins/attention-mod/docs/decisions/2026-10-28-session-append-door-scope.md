# 決策：session.append 只註冊 sec-default 不會跳過的 door

日期：2026-10-28  
狀態：Tom 於 2026-10-29 選定：attachment、hook-context、compaction、tool-message、note 都不註冊。實作於 0.5.2。

## 脈絡

0.5.1 的 `session.append` 不帶 matcher，接收所有 door。在有 managed settings 的機器上，內建的 `cc-plugin-sec-default`（2.1.312）會跳過 user plugin 的這個 hook，終端機每次都出現「hook was skipped」通知。

2.1.312 的 sec-default 規則如下：

- `attachment`、`hook-context`、`compaction`：每一列都跳過。
- `tool-message`：只有來源是 Skill 工具的列跳過。
- `note`：只有來源 tier 是 prepend 或 append 的列跳過。
- `delivery`、`notice`、`response`、`tool-result`：沒有規則，不會跳過。

## 決策

- 註冊改為 `on('session.append', {door: OBSERVED_DOORS}, hook)`。`OBSERVED_DOORS` 是 `delivery`、`notice`、`response`、`tool-result`，也就是面板與摘要會用的 door，扣掉 `PASSED_OVER_DOORS`。
- 不註冊 `attachment`、`hook-context`、`compaction`（Tom 決定）。
- 也不註冊 `tool-message` 與 `note`（Tom 2026-10-29 確認）。這兩個只在部分列被跳過，但目標是「已註冊的 door 不會被跳過」，只有不註冊才能做到。若日後要保留，從 `PASSED_OVER_DOORS` 移除，代價是 Skill 工具的列與 prepend／append tier 的 note 列，會再出現通知。

## 後果

- 面板的「外部輸入」不再顯示 `hook-context`、`attachment`、`compaction`、`tool-message`、`note`。在沒有 sec-default 的機器上，這些 door 以前會顯示，現在不會。
- 「外部輸入」下方的說明文字改為列出這五類（`INPUT_GAP_NOTE`）。
- `DOORS` 不變：`entryFromAppend` 對這些 door 的分類仍然有效，只是 hook 不會再收到它們。

## 驗證

- `tests/registration.test.ts` 直接呼叫 `register`，檢查 `session.append` 的 matcher 正好是四個 door，且不含任何 `PASSED_OVER_DOORS`。先寫、先看它失敗，再實作。
- `claude plugin test .`：150 項通過。
- `claude plugin validate --strict .`：通過，警告種類與 0.5.1 相同；`session.append` 那行顯示為 `session.append{door=?}`。
- 真實終端機（2026-10-29，`--plugin-dir` 啟動）：啟動時沒有 skip 通知；面板標題為 v0.5.2；外部輸入說明已更新；摘要在送出一句話後更新。尚未確認：外部輸入中實際出現 delivery 或 notice 的列（當時只有「尚無」）。
