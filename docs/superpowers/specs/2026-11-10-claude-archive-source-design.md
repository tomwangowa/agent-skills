# Claude 官方目錄轉為封存形式：修正設計草案

狀態：**PROPOSED；尚未核准此設計、實作或新的外部操作**。
使用者 #1 核准的是[離線調查與設計交付](../../validation/plugin-installer/superpowers-archive-source-investigation-proposal.md)。本稿依完整且已確認的範圍提出替代方案，不重問官方來源優先、保留既有 provider、逐次批准等已關閉需求。詳見[調查與取捨](../../validation/plugin-installer/superpowers-archive-source-investigation.md)。

## 建議與界線

採方案 A：**只支援同一次已批准安裝中，可信 Git 目錄轉為可核對的官方封存目錄**。不把 `.gcs-sha` 視為獨立可信憑證；沒有本次 Git anchor（安裝前已封存的來源觀察）時，仍拒絕新安裝。

此範圍是一個既有安裝器的來源驗證修正，不新增服務、不派代理、不做通用 archive manager。CLI 工具不需要視覺設計；研究、設計及執行均沿用目前 session。實作、能力紀錄更新、重跑探測、候選包安裝與模型驗收保留各自界線。既有 `7.0.2` 或其他 provider 一律保留；自有套件與 Codex 行為不得被 archive 規則擴大或改寫。

方案 B 是維持 pending；它也是本稿任何條件未滿時的實際行為。方案 C（啟動時已是 archive、沒有當次 Git anchor）因缺乏 primary evidence，本稿不實作。原生程式的保存形式是觀察值，不能從 marketplace 名稱推定。

## 1. 必須保留與明確變更的規則

| 現有規則 | 本稿處理 |
| --- | --- |
| `catalog_kind=configured-git` 指配置來源；實際 URL 由 native inventory 觀察 | 保留；不把 archive 的存在變造為觀察到 Git origin |
| `PluginSpec.source` 是目錄 URI，payload URI/pin 另存 | 保留，兩者都要核對 |
| 缺少 native acceptance 或完整預期 payload hash 就不寫入 | 保留；本次觀察 hash 不自動提升為預期值 |
| 確認後、執行前來源變動就拒絕 | **完整保留**，包括這時才出現 archive |
| 安裝後只接受 snapshot 完全相等 | 保留為一般路徑；**只為特定 Claude 官方政策新增階段受限的 postcondition** |
| 全部 entry hash／payload pin／版本／內容／config root 仍須相同 | 保留，無關目錄歷史更新不得重用當次批准 |
| `catalog_commit` 歷史紀錄不是每次同 payload 重驗鍵 | 保留；但本次 Git anchor commit 與事後 marker 必須精確相等 |
| Unknown / duplicate / disabled / existing providers | 保留現況，不更新、啟用、重複安裝或降版 |

這個例外只在批准的 install 命令已開始且回傳零之後考慮。不能用它讓確認前變動、自動 source refresh 或其他 provider 的錯誤通過。

## 2. 將觀察、準備狀態與事後證明分開

新增 frozen `CatalogObservation`，只記錄實際讀到的資料：

| 欄位 | 值與限制 |
| --- | --- |
| `catalog_name` | native marketplace identity |
| `configured_repository` | native inventory 實際 URL，可空；不從 target 複製 |
| `config_root` / `catalog_root` | 實際宿主設定根與 native catalog root；空／相對／逃出受管理位置就不合格 |
| `form` | `git`、`official-archive`、`unknown`、`ambiguous` |
| `git_origin` / `git_commit` | 實際本機 Git 觀察；archive 時維持空值 |
| `marker_commit` / `marker_hash` | 實際 marker 解析值及完整 bytes 的 SHA-256；Git-only 時空值 |
| `entry_hash` | 完整原始所選 entry 的 canonical hash |
| `errors` | 觀察失敗原因，不能當成不存在 |

`Inventory` 尾端追加 `catalog_observations=()`，保持既有 positional construction 有效。`ProviderReadiness` 繼續回答**安裝前能否進入預覽**；既有十一項 snapshot key 不假裝同時描述兩種形式。Archive observation 可以存在，但缺少 anchor 時 readiness 仍是 `unverified`。

新增純 `verify_catalog_postcondition(before, after, policy) -> SourceProof`；`SourceProof` 是 frozen 的 `verified`、`method`、`reason`，沒有寫入能力。它只驗來源前後關係，不能取代 native result、scope、enabled、manifest、registry pin 或 payload hash 的檢查。它不得讀檔、執行 CLI、填補缺失 URL 或自行產生 acceptance。

`hosts.py` 負責唯讀檔案觀察；`providers.py` 負責政策與純比對；`planning.py` 只消費 observation 並封存決策；`ui.py` 取得實際觀察交給 `receipts.py` 驗證。原生列舉命令是否可能觸發同步仍未查明，不能把「列舉」名稱當成沒有副作用的證明；未來原生提案須明列這些 vector 與觀察點。

## 3. 安裝前與確認憑證

前置條件全部通過才可建立 anchor：

1. CLI 完整版本、平台、架構與已審閱紀錄相符，預期 payload hash 已完成獨立核對。
2. 官方 URI 為 `https://github.com/anthropics/claude-plugins-official.git`，identity 為 `claude-plugins-official`。
3. 明確取得 Claude `config_root`：有效絕對 `CLAUDE_CONFIG_DIR`，否則以 `Path.home() / ".claude"` 作待核對的宿主預設根；此預設路徑尚須在目標 CLI 的能力案例驗證，native root 不符就拒絕，不能當成觀察值。拒絕空白、相對或歧義值。不可把 native inventory 缺少的 scope 改填 user。
4. 官方 catalog root 必須是該根下的 `plugins/marketplaces/claude-plugins-official`；根以下各部件、manifest、marker 不可是 symlink 或非預期檔案。允許 canonical root 的系統路徑別名，不能藉 resolve 隱藏下面的連結。
5. 觀察到單一 Git 形式，origin/HEAD 合格，且**明確觀察 marker 不存在**。兩種 metadata 同時存在是 ambiguous，不能挑對自己有利的一份；`.git` 的斷鏈也算不安全存在，必須以不追隨連結的觀察辨識，不能因 `exists()` 為 false 就稱為 absent。
6. 完整 raw entry hash、payload URL/pin、預期 manifest/內容都吻合，且沒有既有或不明 Superpowers provider。

anchor 只從本次合格觀察建立，存在記憶體並封入 action；不寫到原生目錄，也不從上次 session／fixture／cache 導入。Action 在既有 preconditions 外追加 `catalog_anchor`（canonical JSON）、`catalog_policy`、`expected_content_hash`，並將 Claude provider 的 `config_root` 納入批准指紋。既有 `provider_state`／`provider_target`／CLI／平台／架構／plugin state 仍保留。

執行前重取來源與 plugin state；**anchor 全等才執行**。如果目錄這時已變為 archive，即使 marker 相同也要停止並重新預覽，不能將尚未開始的操作說成已批准轉換。

## 4. 安裝後的限定判定

一般 Git→Git 仍核對來源與原 snapshot，不放寬任何欄位。對 `claude-official-transition-v1`，只在以下條件全滿時允許 Git→archive：

- 原 action 是單次、新的 Claude `install`，target/CLI/平台/架構/config root/anchor 與批准內容一致，且 native command exit 為零。
- native inventory 仍實際回報同一官方 identity、URI、root；不可用 target 期待值補缺欄位。Git metadata 必須不存在。
- `.gcs-sha` 是受管理 catalog root 下的正常檔案，raw bytes **恰為 40 個小寫 hex、無換行**，符合目前唯一觀察形式；其他格式先拒絕，不能默默 `strip()` 成合格值。
- marker commit 等於本次 anchor 的完整 Git HEAD，所選 raw entry hash、payload URL/pin 都不變。完整 marker bytes 的 hash 也保存在事後證據中，且須等於該 40-byte ASCII commit 的 SHA-256；不一致代表 observation 自相矛盾，應拒絕。這個 hash 只連結 bytes，不賦予來源信任。
- post-install 的實際 user-scope root、manifest identity/version、enabled state、native registry `gitCommitSha` 與全部預期安裝內容逐項吻合。registry 檔案只讀相關選定 entry，不擷取其他設定值。
- native receipt、來源證明與 payload 檢查都通過，才回報該次安裝已驗證；任何失敗保留實際 partial state，不重試、修原生 metadata 或 rollback。

現有 `verify_claude_install` 須額外消費 `CatalogObservation`、action 中的 anchor 與選定政策，再執行完整內容驗證；不能把 `readiness.status='unverified'` 一律改成 true。Archive 的 Git origin 仍記作未知，證明方法是 `anchored-archive`，不是 `git`。這只表示經該政策核對的安裝結果，不表示入口或七項模型行為通過。

同次轉換的政策可以定義整個已批准 install／事後讀取群組的前後證明，但啟用前須查明原生保存方式及觀察 vector 的效果。現有案例未隔離單一觸發點，也沒記錄安裝前 marker 缺少，不能直接視為符合本節的完整能力證據。

## 5. 政策、schema 與相容界線

建議新 runtime 的 bundled `catalog.json` 為 schema **3**，與 R4 schema 2 分開；`installer/providers.json` 仍為 schema **2**，因 target 配置來源與 payload 欄位沒有改。Provenance／dependency mapping 維持 schema 1。

Native acceptance index 升為 schema **2**，既有 tuple 欄位外要求一個封閉的 `catalog_policy`：Claude 可為 `strict-git-v1` 或 `claude-official-transition-v1`，Codex 沿用明確的 `codex-native-v1`。沒有 policy 的舊 record 不可取得轉換權限；新 runtime 拒絕舊 acceptance schema。精確 target tuple 重複的 record 一律拒絕，避免暗中挑選較寬鬆政策；歷史 catalog commit 不成為相同 payload 的再驗收鍵。

`target_accepted` 仍只判定靜態 target 是否有精確紀錄；`installation_accepted` 再要求本次來源 form 與政策允許的**前置條件**。Postcondition 才可使用 declared transition。Policy 是 runtime 內的封閉規則，不是使用者可放入任意 predicate／URL 的執行語言。

本稿不新增真的 record、不更改產品 hash。未來紀錄須連到經審閱的來源及 materialization 證據；單純 native exit、文件存在或 `catalog_policy` 字串不能取得能力。R4 的 ZIP/runtime/catalog 保持原樣，新 runtime 不讀取或改寫它，也不把舊 synthetic acceptance 轉為 native 紀錄。

## 6. 自有套件回歸修正必須獨立

[planning.py](../../../runtime/agent_skills_installer/planning.py) 第 92–100 行誤將 Superpowers-only `readiness.snapshot` 用在 `provider=None` 的自有來源，兩個 host 都已重現 `AttributeError`。

未來最小修正是：自有來源沿用自有 source action 的 preconditions，不讀取 provider/anchor/policy；只有已驗證的外部分支才加新欄位。不以 catch 例外或虛造 readiness 掩蓋。測試必須包含直接規劃缺來源，以及 UI 拒絕來源準備後仍能顯示 skipped／pending、沒有 native mutation，不能只測來源存在的成功路徑。本輪不改程式，R4 仍有這個未修缺陷。

## 7. 測試、啟用門檻與剩餘證據

[測試矩陣](../../validation/plugin-installer/superpowers-archive-source-test-matrix.md)是未來驗收規格，**不是本輪已通過的測試**。須先重現缺陷，再做正常／失敗分支、具名 provider 隔離、declined consent、一次嘗試、封裝移位及舊 schema 拒絕等檢查。

啟用 `claude-official-transition-v1` 至少需要：

1. 審閱本設計及後續實作計畫；修正自有來源回歸並完成相應離線測試。
2. 取得可追查的 archive 來源／生命週期 primary evidence，或另行批准精確、逐 vector 觀察的能力探測，以補足原生規則與影響範圍。不能從 marker 名稱自行推導傳輸協定或簽章驗證。
3. 另行核准取得獨立固定上游 tree，與原生 materialization 的每個檔案比對；`.git` 等來源控制資料是否排除，必須有明確契約與原始來源佐證，不新增為了通過而設的任意忽略規則。
4. 核對來源／pin／manifest／完整內容／原生結果及所有前後觀察後，才審閱精確 acceptance record；再建新候選包並另批未修改安裝器驗收。七項行為測試仍需模型／成本批准。

以上任一門檻未滿都不開放 native write。草案的完整性可離線驗證，archive 相容性與功能完成度目前仍為 **NOT VERIFIED**。
