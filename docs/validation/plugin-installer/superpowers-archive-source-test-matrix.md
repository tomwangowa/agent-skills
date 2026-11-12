# Claude 官方 archive：待實作的正常／失敗測試矩陣

狀態：**測試規格；不是測試通過紀錄**。對應[修正設計草案](../../superpowers/specs/2026-11-10-claude-archive-source-design.md)。本輪只有重讀既有檔案、核對保存一致性，以及重現自有來源規劃例外；下列新功能測試尚未實作或執行。

## 證據與測試資料規則

- 三份 `observed-claude-*` 官方來源 fixture 保持原始觀察語意；before-marker-absence 與轉換單一觸發點未觀察，不能事後補成真實證據。
- Synthetic fixture 可在臨時目錄建立 `.git` / marker / manifest / payload，用於明確標示的單元／流程測試；不寫原生 caches、不執行真實 CLI、不複製個人配置、也不寫 production acceptance。
- 完整既有 runtime 的規劃與 executor／UI 透過程序邊界替身執行，驗證真實檔案是否被保留、是否建立、結果狀態與命令嘗試次數。不得只比對 source 字串或預設 mock 回傳值。
- 判定 `zero mutation` 時須檢查命令紀錄與檔案；判定 partial 時須檢查已留下的檔案、沒有第二次 source/install，也沒有 uninstall／repair／rollback。
- 每條 release／native assertion 必須連到後續另批的真實案例；synthetic 的 green 只證明該層程式行為。七項模型功能不在這份離線矩陣內。

## B：自有來源與隔離回歸

| ID | 輸入／操作 | 未來必須成立的結果 |
| --- | --- | --- |
| B01 | 分別以 Claude / Codex 自有 spec、有效 CLI/config root、缺少 `tomwangowa` 來源呼叫 `make_plan` | 不拋例外；各產生一個自有 source-add proposal，沒有 provider/anchor/policy 欄位。**目前兩個 host 都已重現 AttributeError，未修。** |
| B02 | 多個自有套件共享缺少來源 | 同一 host/URI 只產生一個 source action；全部 affected items pending；不讀 `readiness=None` |
| B03 | UI 拒絕來源準備，之後確認安裝 | 不 crash；回報來源未就緒與 partial exit；source/install 零次；不將 source-add 放進 final install consent |
| B04 | 一個來源 pending、另一個已知自有套件來源完整且選定 | 後者可依自己的批准執行；前者 pending；回傳 partial；不得因 archive 狀態全域阻塞 |
| B05 | SP 來源／acceptance 不明，或已有維護者 `7.0.2`、停用／重複 provider | 全部 SP 既有檔案保留；SP mutation 零次；自有來源規劃／驗證不消費 SP 欄位 |

## O：原始觀察分類

| ID | 輸入／操作 | 未來必須成立的結果 |
| --- | --- | --- |
| O01 | 明確 Git-only，Git origin/HEAD/entry/managed root 齊全，marker 明確不存在 | 可建立本次 anchor；所有值來自觀察；不是僅憑 `ready` 字串通過 |
| O02 | 一開始就是 archive，marker/entry 即使與舊觀察吻合，沒有當次 Git anchor | observation 可列出，readiness 仍 unverified；不新增／刷新／修理來源，不提只為 SP 的依賴安裝 |
| O03 | `.git` 與 `.gcs-sha` 同時存在，或 `.git` 是斷鏈 | ambiguous；不得依其中一份恰好吻合而 fallback；不建立 anchor |
| O04 | Git/config/HEAD 缺少、Git origin 不符、entry 重複／缺少或 raw URL 缺少 | unverified；空值不複製 target URI；全域 inventory 損壞仍按原 host-wide error 處理 |
| O05 | marker 是 symlink、directory、非一般檔案、超長、UTF-8 BOM、短值、uppercase 或 40hex 加換行 | 全部拒絕該 archive 政策；不得 strip/normalize 成可信 commit |
| O06 | 路徑為相對／外部 root、子路徑 symlink；另有 macOS root alias 正常案例 | 逃出與連結拒絕；真正系統 root alias 可 canonicalize，但不能隱藏 root 以下的連結 |

## P：批准與執行前

| ID | 輸入／操作 | 未來必須成立的結果 |
| --- | --- | --- |
| P01 | 本次完整 anchor、target、content hash、record policy 被封存 | 改任一值都改變 fingerprint；executor 拒絕與批准不符的 plan |
| P02 | 批准後、install 啟動前 Git 轉 archive，marker 與 entry 都相同 | precondition 失效，install 零次；不能套用 post-only 轉換規則 |
| P03 | 執行前改 origin、HEAD、entry/pin、CLI 完整字串、平台、架構或 Claude config root | 拒絕並要求新預覽；零 install；架構別名與同版本範圍不自動相容 |
| P04 | 批准後出現另一個 SP provider／orphan cache／link cache parent | 保留個人或部分狀態；零 install；不能自動啟用或移除 |
| P05 | 從上次 session、已存在 archive 或 release fixture 匯入 anchor | 不承認為本次 Git 觀察；零新安裝。純 helper 即使測到資料一致，也不得替執行層建立歷史權限 |

## A：能力政策與 schema

| ID | 輸入／操作 | 未來必須成立的結果 |
| --- | --- | --- |
| A01 | 沒 record、未知內容 hash、缺欄位或來源政策不合 host | SP 不寫入，不先下載再假設會可安裝；其他已知套件依原規則 |
| A02 | 新 runtime 載入 catalog schema 2 或 acceptance schema 1 | 明確拒絕混用，不將舊紀錄默認為允許 transition |
| A03 | acceptance schema 2 的 unknown policy、wrong host policy、重複 target tuple | 拒絕 index；不依順序選較寬鬆紀錄 |
| A04 | `strict-git-v1` 紀錄遇 post archive | install 後回報 partial/unverified，來源形式未獲授權；沒有 retry |
| A05 | `claude-official-transition-v1` 的精確 tuple | 只取得本稿 post-only 能力；cold-start archive 仍不會 ready，也不能套用到 Codex／其他 marketplace |
| A06 | 歷史 record catalog commit 改變，但 entry/payload 完全相同；另測本次 anchor 與 post marker 不同 | 前者不強迫重驗相同 target；後者仍必須拒絕，不能把歷史規則搬到當次批准 |

## T：安裝後正常與失敗結果

| ID | 輸入／操作 | 未來必須成立的結果 |
| --- | --- | --- |
| T01 | 合格 Git→Git，未改來源、payload、有效 native result / user enabled state | strict path 正常驗證；archive 邏輯不干擾 |
| T02 | 合格本次 Git anchor→archive，政策正確，raw marker 恰 40hex、commit/URI/root/entry/pin 都相同，payload 完整吻合 | `SourceProof.method=anchored-archive`；Git origin 在 after observation 仍空；全部 postconditions 通過才可回報該次安裝已驗證 |
| T03 | marker 同值但 URI/marketplace/root/entry/pin 任一變動，marker hash 自相矛盾，或 marker 本身變成缺少／不符／ambiguous | partial/unverified；不能只比較 SHA 或 directory name 放行 |
| T04 | marker/registry pin 相符，但 payload 多／少／改一檔，manifest 錯版或 symlink | 完整內容驗證失敗；檔案保留、一次嘗試；不得增加忽略規則 |
| T05 | native install JSON 空／錯 ID／錯 scope，inventory disabled／project scope／missing root，或 registry pin 缺少／錯誤／重複 | partial/unverified；`SourceProof` 通過不代表這些條件也通過 |
| T06 | install nonzero／timeout／keyboard interruption，即使 archive/entry 最終相符 | failed 或 unverified partial，不能報 installed；不 retry，不補寫 registry |
| T07 | source observation / proof helper 只能取得部分欄位，或被餵入 `ready` label + 不完整內容 | 缺證據即拒絕；helper 不發出 subprocess、不讀檔、不補期待值 |
| T08 | source proof 合格，但要求宣稱重啟後入口／七項行為通過 | 仍顯示 entries/behavior NOT VERIFIED；未另外批准不得啟動模型／代理／hooks |

## I：整合與發布界線

| ID | 輸入／操作 | 未來必須成立的結果 |
| --- | --- | --- |
| I01 | 新 bundle 建置與移位，CLI cancel / decline transcript | 搬離 repo 仍用自身 runtime/catalog schema 3、acceptance schema 2；來源／安裝批准分開，不提供 --yes 捷徑 |
| I02 | 觀察形式受支援但 native acceptance／來源契約證據尚未受審閱 | production `records: []` 及未知 payload hash 仍阻擋 write；不能從 synthetic case 自動產生 record |
| I03 | Codex 自有 R3 receipt、官方 native-managed 分支、disabled/unknown scope 及更新請求 | 原有拒絕／驗證語意不擴大；Claude marker/policy 不適用；具名 query 不擴大成 global remote query |
| I04 | R4 artifact、四份 stash、既有 native case；建立新候選包 | 不覆寫、清理或混搭；新包另取唯一檔名與輸入指紋，無自動 commit/push |
| I05 | 真實能力／未修改候選包／正常與失敗模型 case | 各自需新的精確提案、批准及證據；離線測試 green 不替代原生與行為驗收 |

## 實作前後的證據要求

先重現 B01／B03，再修改自有來源最小分支；對新來源政策先建立會失敗的正常／拒絕案例後才改產品。合格 fixture 若驗證器被刪除或一律回 true，矩陣中的拒絕案例必須失敗；一律回 false 時，正常案例必須失敗。

完整原生能力仍缺 marker 形成／來源契約及 payload 的獨立固定上游對照；不得因有 T02 synthetic case 而填 record。後續原生探測要在每個 vector 前後記錄兩種 metadata 是否存在、marker bytes、entry、registry 與 payload，並保留失敗結果。這份矩陣本身沒有授權重跑任何外部動作。
