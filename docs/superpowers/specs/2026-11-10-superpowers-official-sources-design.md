# Superpowers 官方來源補充設計

- 狀態：**使用者於 2026-11-10 以 #1 同時核准補充設計、計畫與離線實作；原生／模型測試、代理、commit 與 push 仍未批准**。
- 核准範圍：依[實作計畫](../plans/2026-11-10-superpowers-official-sources.md)執行離線任務 1–4，準備任務 5 的提案；外部操作保留各自的批准點。
- 延續：[原設計](2026-11-09-cross-platform-plugin-installer-design.md)、[來源查核](../../validation/plugin-installer/superpowers-official-source-strategy.md)。不重開已確認的跨平台、選單與資料保留需求。
- 基準：`fe55c04bf9202fe82f1a68b7f5985305c82249f0`；既有 R3 候選包保持原樣。

## 目標與已確認決定

各 CLI 優先使用自己的官方目錄，版本可以不同，再分別驗收所需功能。Superpowers 維持強烈建議、預設不勾選。官方收錄不寫成官方主動推薦，也不當作相容性證明。

本次補的是「目錄來源」與「套件來源」分開的辨識、原生準備狀態、保守的安裝／驗證流程，以及每個版本的驗收紀錄。七個自有套件、兩個 Claude 額外項目、日誌設定、啟動程式與 CLI 安裝政策沿用原設計。

| CLI | 官方目錄與來源 | 套件來源 | 目前查核版本 |
| --- | --- | --- | --- |
| Claude Code | `claude-plugins-official`；`https://github.com/anthropics/claude-plugins-official.git` | `https://github.com/obra/superpowers.git`，entry 固定 `bb92a77741419a4ab5f06e711a283343f1ada0c3` | `7.0.0` |
| Codex | `openai-curated`；原生管理的 `https://github.com/openai/plugins.git` 目錄 | 目錄內 `./plugins/superpowers` | `6.3.0` |

版本是 2026-11-10 的公開 Git 來源快照，不是帳號型遠端目錄的查詢結果。每份候選包明列預期版本、所選 entry 指紋、套件 commit／內容指紋。目錄 commit 另作原生來源與操作時點證據；只有其他套件改變時，不要求重驗同一份 Superpowers 內容。所選 entry／套件內容改變則不能沿用舊驗收或靜默跟隨最新版。Codex 尚缺一個完整來源快照與內容指紋；資料不齊時停用該安裝分支，不填猜測值。

## 採用方向與取捨

採來源查核的方案 A 作為本設計候選：各 CLI 分開處理原生目錄與安裝結果，可核對時才提供自動安裝；未就緒時提供原生指引，其他獨立套件照常處理。

方案 B 是兩邊都只提供手動安裝指引。它比較小，但會把原本的自動安裝需求留成缺口，因此只作為尚未通過某一原生分支時的明確待辦狀態，不宣稱已完成自動安裝功能。

主要失敗情境是官方目錄更新、受管理狀態不完整，或同名套件來自其他來源。處理方式是讓對應 Superpowers 項目保持待設定／未驗證，保留現況；不建立改名的官方目錄、不回退維護者來源，也不將來源問題擴大成其他已知套件的失敗。

## 資料與模組邊界

沿用 Python 標準函式庫與 frozen dataclasses，不新增服務或通用來源執行語言。新增一個 `providers.py`，只處理 provider 對應、驗收紀錄與純決策；檔案及 native inventory 讀取仍在 `hosts.py`，命令仍由已確認的 executor 執行。

`PluginSpec.source` 明確指**目錄 repository**，自有套件的現有值不變；新增可空的 `provider: ProviderSource`。`ProviderSource` 欄位如下：

| 欄位 | 語意 |
| --- | --- |
| `catalog_kind` | `configured-git` 或 `native-managed` |
| `catalog_repository` | 上表完整 Git URL；不能只依 marketplace 名稱填入觀察結果 |
| `payload_kind` | `catalog-relative` 或 `git` |
| `payload_repository` | 外部 Git 套件 repository；相對來源為空 |
| `payload_commit` | 外部 Git entry 固定的完整 commit；相對來源為空 |
| `payload_path` | 相對來源的 `./plugins/superpowers`；外部 Git 為空 |
| `entry_hash` | 所選原生 marketplace entry 完整 JSON 的 canonical SHA-256；未知則為空，不能免檢 |

`PluginSpec.version` 仍是套件 manifest 版本，`content_hash` 仍是完整預期安裝內容指紋；不混用 Codex 快取版本。未知內容指紋以空值表示並拒絕新安裝，不把它視為免檢。

`Marketplace` 追加 `provenance_kind`（`configured-git`／`native-managed`／`unknown`）與 `commit`。既有 `source` 缺少時維持空值，不把預期 URL 複製成已觀察 URL。

新增 `ProviderReadiness(name, status, reason, snapshot)`，其中 `snapshot` 是不可變、已排序的 `(key, value)` tuple。`Inventory` 追加 `provider_readiness`。這讓官方目錄的局部未知只限制 Superpowers；全域命令失敗或整份 inventory 損壞仍走既有 `errors`，不假裝可以辨識其他套件。

snapshot 固定含 `catalog_name`、`catalog_kind`、`catalog_repository`、`catalog_root`、`catalog_commit`、`entry_hash`、`payload_kind`、`payload_repository`、`payload_commit`、`payload_path`、`payload_hash`；未知值用空字串，不是驗證通過。`entry_hash` 使用原始 entry 的相對 source，而非解析成電腦絕對路徑後的物件。Claude 的外部固定 Git entry 不在安裝前額外下載 payload；其觀察值 `payload_hash` 可空，但預期內容指紋、固定來源／commit 與已審閱的安裝能力證據必須齊全，安裝後仍核對完整內容。

新增 `NativeAcceptance(host, cli_version, platform, architecture, catalog_name, catalog_commit, entry_hash, manifest_version, content_hash, evidence_ref)`。合格組合精確比對目錄 identity、entry 與套件內容，不用版本範圍；`catalog_commit` 記錄當時證據，不要求日後目錄中無關套件的 commit 完全相等。操作中的實際目錄 commit 仍須可核對、封存並重查。`installer/provider-acceptance.json` 只存經審閱紀錄，初始 `records` 為空；不能由成功 exit code 自動產生「已相容」旗標。

`cli_version` 使用 native `--version` stdout 去除首尾空白後的完整值；`platform` 是 `macos|windows|linux`，`architecture` 是當地 `platform.machine().lower()`。不自行把不同版本字串或架構別名當作同一個已驗組合。`catalog_commit` 是當時完整 40-hex 證據，`entry_hash`／`content_hash` 是完整 64-hex；缺值不能建立合格 record。`evidence_ref` 是非空、可追查的發行驗收文件參照，不能從檔名或是否存在就推論驗收通過。

`installer/providers.json` 與封裝 `catalog.json` 升為 schema `2`，外部項目分成一筆 Claude 與一筆 Codex target。R4 runtime 拒絕 schema `1`；R3 原包仍使用自己的 runtime/catalog，不覆寫或混搭。依賴映射 schema 維持 `1`。

providers schema `2` 保留 root `repository`、`marketplace`、`external`。每筆 `external` 使用單一 `host`，以及 `name`、`marketplace`、`source`、`version`、`skills`、`notices`、`content_hash`、`provider`；`skills`／`notices` 沿用字串陣列，`provider` 是上表欄位的物件。舊 `hosts` 陣列不接受。JSON 的未知 `content_hash: null` 轉為 runtime 的空字串，會阻擋寫入。`entry_hash` 以 `json.dumps(entry, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')` 計算；不忽略 entry 欄位。

## 原生辨識與既有 provider

Claude 必須同時核對官方目錄的實際 repository、目錄 entry 指向的套件 repository／commit，以及安裝結果的 manifest、來源與內容。不能到官方目錄內套用自有套件的相對路徑規則。若 native 安裝含有目前指紋規則無法解釋的額外檔案或連結，該分支保持未驗證，不新增寬鬆忽略規則。

Codex `0.167.0` 把 `openai-curated` 設為保留名稱。一般 Git marketplace-add 不能準備它；安裝器不得改寫原生 `.tmp/plugins`、`.tmp/plugins.sha` 或 installed cache，也不得呼叫私有同步函式。只消費由 Codex 自己準備好的官方目錄。可核對的條件包含原生 marketplace identity、CODEX_HOME 下的受管理位置、目錄 commit receipt、manifest／entry 及預期內容；任一缺少都不能僅憑路徑名稱取得信任。

只使用已查核的具名 native inventory 讀取。Codex `0.167.0` 的 CLI 程式碼會對非 global 的具名 marketplace 跳過遠端 global catalog 查詢；不把這個特性擴大到其他版本或未指定來源的查詢。不開啟 App Server 或模型 session 來偽裝成離線盤點。

盤點範圍包含可唯讀辨識的既有官方與維護者 Superpowers provider。維護者來源僅供保留辨識，不是新安裝 fallback。無法安全檢查的來源標為不確定，不能將未檢查的 provider 當作不存在。

已知既有 Superpowers 一律保留，不更新、移除、啟用或降版，包括比官方版本新的 `7.0.2`。重複 provider、停用狀態或未知管理範圍也保留並回報未驗證；不額外建立第二份安裝。這次不開放 Superpowers 更新分支。

## 準備狀態與一次性計畫

| 狀態 | 條件與結果 |
| --- | --- |
| `preserved` | 已辨識既有 provider；不產生新安裝／更新命令，不宣稱功能已通過 |
| `needs-native-setup` | 官方目錄尚未由宿主準備；顯示原生指引，這次略過 Superpowers |
| `unverified` | 來源、內容、現況或精確 native 驗收紀錄不足／衝突；不寫入 |
| `ready` | 沒有既有或不明 provider，來源觀察條件齊全；另須通過 native 安裝能力紀錄比對，才可進入安裝預覽 |

Claude 官方目錄缺少時，只有預期 target 已有相符 native 安裝能力紀錄，才可另提來源新增計畫，沿用預覽／確認；新增不是套件安裝確認。能力紀錄為空時不先下載目錄再停在不可安裝狀態。已有官方目錄但版本／內容不符時不自動刷新，因為刷新也會影響目錄中其他套件的後續操作。Codex 缺官方目錄時只顯示 `/plugins` 原生設定指引，直到初始化方式另經查核與批准。未就緒的 Superpowers 不觸發只為該項服務的依賴代裝；其他選定項目仍各自處理。

確認憑證納入 provider descriptor、readiness snapshot、CLI／平台／架構、原生驗收組合與 CODEX_HOME，以及既有的套件／來源狀態。執行前重新取得 snapshot；改變就停止該項，不沿用舊確認。所有會新增／改動來源或套件的命令仍最多嘗試一次。

## 安裝後驗證

Claude 以 user-scope native inventory 的實際 root 核對官方來源與套件 manifest／完整內容。Codex 沿用 R3 的真實 JSON add receipt，但擴充對已準備好的官方目錄的來源檢查，不把 `scope=user` 填入缺少的欄位。

Codex `0.167.0` 的官方 cache 版本可為目錄完整 SHA 的前 `8` 個字元。驗證時 receipt 的 cache version、實際 cache root、inventory cache version 與目錄 receipt 必須相符；安裝目錄內的 manifest 另外核對 `6.3.0`，不能將兩種版本相等設為成功條件。完整 payload 指紋仍必須符合候選包的預期。

保留 R3 對相對／不符 root、symlink、未註冊快取、改變的設定目錄與內容的拒絕。Codex 新安裝及官方來源的邊界按已查核的 CLI 版本限制；新版本不自動沿用。

命令成功但事後證據缺少時保留部分寫入並回報 `unverified`，不重試、不自動卸載。安裝成功、native 入口可用及行為驗收是三種結果，不合併成「全部相容」。

## 所需功能的驗收

七個入口是 `writing-plans`、`test-driven-development`、`systematic-debugging`、`executing-plans`、`subagent-driven-development`、`requesting-code-review`、`finishing-a-development-branch`。兩個來源都已讀到這些檔案，仍不能當作目前 CLI 已暴露入口。

| 證據層 | 完成條件 | 不足時的狀態 |
| --- | --- | --- |
| 安裝 | 合格原生操作、來源／manifest／完整安裝內容、enabled inventory 與退出碼均符合 | 待設定或未驗證，不開放未驗證的自動寫入分支 |
| 入口 | 由目前宿主暴露的 native metadata 確認入口與 owning provider／版本 | 入口未驗證，不以檔案、快取或 registry 代替 |
| 行為 | 每個選定分支在新建小型測試專案上符合[來源查核的七項驗收](../../validation/plugin-installer/superpowers-official-source-strategy.md)，包含正常／失敗條件 | 對應流程保持未驗證，不宣稱整包相容 |

功能結果另按 CLI、plugin 版本、來源 commit、平台與分支記錄，不能由 `NativeAcceptance` 的安裝通過紀錄推導。實際派子代理、模型 session、外部 reviewer、hook 信任及 commit／push／merge 各保留明確批准邊界。退役 Gemini 不路由；Codex review 仍先走自己的 native reviewer。

原生安裝 adapter 的 capability probe 與完整候選包驗收分兩階段。先另行批准最小 native probe，確認來源與安裝內容契約，才新增審閱過的安裝驗收組合；之後還要另行批准使用未修改候選包的安裝器驗收。兩次目的與證據不同，不能把 probe 的成功當作候選包成功，也不自動重跑外部動作。

行為測試會使用真實模型、消耗 tokens；執行前另列 CLI／模型、輸入檔案、提示、預期修改、派代理範圍、成本界線與停止條件。本輪沒有批准這些操作。

## 完成條件與未驗證項目

離線階段須證明來源辨識、部分不明狀態隔離、保留既有 provider、確認失效、兩種版本分離、錯誤路徑拒絕及封裝可重現，並維持自有套件的回歸檢查。新 candidate 不取代 R3。

`NativeAcceptance` 初始空清單是明確的保守狀態，不能據此宣稱已完成 Superpowers 自動安裝。完整交付仍需通過各目標 CLI／平台的原生 candidate 安裝及選定功能驗收。

目前未驗證：官方 Superpowers 的完整安裝內容指紋與 materialization 契約、Codex 官方目錄在全新環境的初始化、目前宿主的入口註冊、七分支行為、Windows／Linux 與跨版本組合。任何需要額外 ignore、原生目錄寫入或替代來源的解法，均屬後續設計變更，不能在實作時默默放寬。

## 審閱邊界

這份設計與計畫已由使用者 #1 共同核准，離線實作依目前 session 自行執行；這次核准不包含子代理、stage、commit、push 或新的外部測試。原生能力、未修改候選包安裝與模型功能驗收仍各自需要具體提案及批准。
