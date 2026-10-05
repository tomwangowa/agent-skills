# 面板配色設計（0.3.0）

日期：2026-10-05  
狀態：Tom 已於 2026-10-05 確認書面規格，可作為實作依據。  
上層設計：[Attention Mod 設計](2026-10-03-attention-mod-design.md)、[外部輸入欄位](2026-10-04-external-inputs-design.md)。本文件只改面板的呈現方式，不改資料來源、摘要規則或外部輸入的收錄規則。

## 目的

讓面板一眼就看得出「現在需不需要我」。參考 Tom 喜歡的 resource-dash Mod：用有色框線分區、中括號標題、加了顏色的狀態符號，次要資訊用灰色。

2026-10-05 寫計畫時對齊既有測試的字面調整：dock 欄位名保留「：」、摘要 meta 沿用原字串、● 放在欄位名前面；不改設計意圖。

## 已確認的決定

1. **依位置切換版面**：`e.props.placement === 'dock'` 時，用三個有框區塊；其他值一律用無框、只上色的版面（inline）。
2. **顏色的意思**：摘要區塊固定用藍色，外部輸入區塊固定用洋紅；「即時」區塊依狀態變色，執行中是綠、等你是黃、閒置用終端機預設色。狀態點 ● 的顏色：執行中綠、等你黃、不明和閒置用終端機預設色、失敗紅。「摘要更新失敗」用紅字。
3. **標題寫成 `[ 摘要 ]`、`[ 即時 ]`、`[ 外部輸入 ]`**，不放 ▾，也不做收合。
4. **用終端機具名色**（blue、green、yellow、magenta、red），不用固定色碼，讓顏色跟著終端機主題走。「閒置／次要」（`muted`）不設顏色，用終端機前景色；次要文字用 `dimColor`。2026-10-05 PoC 實測：`gray` 在 dock 的灰底上看不見，theme key（inactive、subtle、success、warning、error）不會上色，所以都不用。dock 的灰底是 Claude Code 全螢幕模式（或 Warp 主題）本身的底色，Tom 決定不處理。
5. **附註搬進對應的框裡（只有 dock）**：「脈絡與證據更新：N 秒前」放在摘要框標題列的右側，「距離最近事件」放在即時框標題列的右側，「有新活動」和「摘要更新失敗」放在摘要框內。
6. **dock 拿掉面板內的大標題和分隔線**，因為面板外框本來就會顯示 `ui.open` 給的標題。
7. **框線用圓角**（`borderStyle: 'round'`）。
8. **inline 的行數和欄位順序跟 0.2.0 一樣**，只加顏色。
9. **「動作」新增失敗提示**：最後一個工具失敗、而且沒有工具在跑時，● 顯示紅色。

## 資料結構（`hooks/view.js`）

`paneRows(state, now)` 回傳 `{title, sections}`。區塊依序如下：

| id | label | tone | meta | 內容 |
| --- | --- | --- | --- | --- |
| `summary` | 摘要 | `accent` | `脈絡與證據更新：N 秒前` 或 null | rows：目標、脈絡、證據；notes：有新活動（`muted`）、摘要更新失敗（`danger`），沒有就不放 |
| `live` | 即時 | 依狀態 | `距離最近事件：N 秒` 或 null | rows：動作、需要你，各帶 `dot` |
| `inputs` | 外部輸入 | `input` | `N 筆` 或 null | rows：`{text, excerpt}`；`empty` 沿用 0.2.0 的文字 |

狀態對應色調的規則如下，由上往下比對，先符合的先用：

- 即時區塊的 `tone`：有等待 → `warning`；有工具在跑 → `success`；其他 → `muted`。
- 「動作」的 `dot`：有工具在跑 → `success`；最後一個工具的狀態是 `error` → `danger`；其他 → `muted`。
- 「需要你」的 `dot`：有等待 → `warning`；其他 → `muted`。

`paneLines` 從 `sections` 產生 inline 版面的純文字，內容與 inline 相同（外部輸入的 `N 筆` meta 只在 dock 顯示，inline 不多加一行）。版面一律用 id 取區塊（`sectionById`），不依賴區塊順序。

## 顏色對應（`hooks/theme.js`，新模組）

這是純函式，不依賴 `$`：`accent → blue`、`success → green`、`warning → yellow`、`danger → red`、`input → magenta`；`muted` 不在對應表裡，跟未知色調一樣回傳 `undefined`。`colorFor(tone)` 遇到沒見過的色調會回傳 `undefined`（使用終端機預設色），不會丟出例外。

## 繪製（`hooks/register.js`）

Pane render 只負責分流：先 `paneRows`，再 `$.ui.resolve(e)`，然後依 `placement` 呼叫檔案頂層的 `drawDock(view, els)` 或 `drawInline(view, els, bodyColumns)`（inline 的分隔線需要寬度，繪製函式又不能拿 `$`），最後由 handler 補上「收起」按鈕（它需要 `$`）。兩個繪製函式只接收 view 和元件建構函式，不接收 `$`，以符合 Mod 靜態分析的限制。

- **dock**：每個區塊是 `Box({borderStyle:'round', borderColor: colorFor(tone), paddingX:1, flexDirection:'column'})`。標題列是 `flexDirection:'row'` 加上 `justifyContent:'space-between'`，左邊是粗體 `[ label ]`，右邊是用 `dimColor` 畫的淡色 meta。
  - 摘要框：欄位名寫成「目標：」，用區塊色、粗體，內容可以換行。
  - 即時框：每列開頭是 `●`（顏色由 `dot` 決定），接著是「動作：」「需要你：」。
  - 外部輸入：每筆截成一行，節錄用 `dimColor`。
- **inline**：保留標題、分隔線，以及「目標、脈絡、動作、證據、需要你、外部輸入」的順序。
  - 欄位名上色：目標、脈絡、證據用 `accent`；動作、需要你用即時區塊的色調；外部輸入用 `input`。
  - 動作和需要你的欄位名前面加 `●`（「● 動作：…」），跟 dock 一致，原本「動作：正在執行…」的文字仍然是連續的。
  - meta 和 notes 放在最下面，notes 依 tone 上色；`muted` 的 meta 和 notes 加上 `dimColor`，跟 dock 的 meta 一致。

## 測試與驗證

**計畫第一步是 micro-PoC**：在 scratchpad 做一個極簡 Mod，畫出 `round` 框、六種具名色的框線和文字、`dimColor`，以及左右對齊的標題列，請 Tom 用 `--plugin-dir` 實機截圖確認。有任何一項無效，就在這一步換掉，例如換成 `single` 或其他具名色。

自動化測試：
- `theme.test.ts`：五種對應正確，`muted` 和未知色調回傳 `undefined`。
- `view.test.ts`：區塊順序、即時區塊色調三條規則（等待優先於執行中）、動作的點、meta 和 notes 放在正確區塊、`paneLines` 與 inline 內容相同、依 id 取區塊不受順序影響。
- `integration.test.ts`：
  - dock 有三個 `round` 框，顏色分別是 blue、即時色（閒置時為 undefined）、magenta；有等待時即時框是 yellow。
  - inline 沒有框，欄位名的顏色正確，行數跟 0.2.0 一樣。
  - 同一份狀態下，dock 和 inline 的文字都包含所有欄位的值。
  - 原本的「標題、分隔線、粗體欄位名」結構測試改成只檢查 inline。

實機驗證（先停用全域安裝的版本）：
1. 寬終端機 dock 的顏色正確；跑工具時即時框變綠，有等待時變黃。
2. 窄終端機 inline 的行數沒有增加，「收起」看得到。
3. Claude Desktop 的繪製結果：只記錄，不保證。

## NOT VERIFIED

- `borderStyle` 是否接受 `'round'`、`color` 和 `borderColor` 是否接受具名色：型別只寫了 `string`，交給 micro-PoC 確認。
- dock 寬度的實際繪製效果，以及 Claude Desktop 的顏色與框線支援。

## 發布

版本改成 0.3.0。在 `你在忙什麼` repo 跑 L1 gate、`code-review-claude` 後 commit；agent-skills 執行 `git subtree pull` 後 push；最後執行 `claude plugin update attention-mod@tomwangowa` 並重新啟動。每一步動手前都要先問 Tom。

## 不做的事

收合／展開、自訂主題設定、固定色碼、改變 inline 的欄位順序或行數、「收起」以外的新互動。
