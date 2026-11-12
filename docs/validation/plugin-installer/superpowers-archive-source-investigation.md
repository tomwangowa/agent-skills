# Claude 官方封存來源：離線查核結果

日期：2026-11-10。狀態：**調查已交付；建議方案待審閱，未批准實作或啟用**。
使用者以 #1 核准[離線調查範圍](superpowers-archive-source-investigation-proposal.md)。本輪未呼叫 Claude/Codex CLI、網路服務、模型或子代理，未修改產品程式、原生目錄、驗收資料或 R4。

## 結論與證據範圍

「官方來源在原生操作後仍保留 `.git`」已被[實際案例](superpowers-native-claude-run-2.md)推翻；「只要 `.gcs-sha` 與舊 HEAD 相同就可相信來源」則沒有足夠證據支持。建議設計一條**同次操作的來源轉換驗證**：安裝前已取得可信 Git 觀察，安裝後只容許有完整對照證據的特定封存形式。啟動時已是封存目錄、缺少前次 Git 證據的情況，維持未驗證。這是有條件的設計建議，現在仍不得開放安裝。

可交付設計不等於現有資料足以啟用它。目前另缺原生轉換規則及固定上游完整內容的獨立核對。不能用本次觀察的 hash 同時當成預期值與驗證結果。具體規則見[修正設計草案](../../superpowers/specs/2026-11-10-claude-archive-source-design.md)，案例見[測試矩陣](superpowers-archive-source-test-matrix.md)。

## 查核來源

| 來源 | 可證明的範圍 |
| --- | --- |
| [原生轉換 fixture](../../../tests/fixtures/installer/observed-claude-official-catalog-transition.json) | 原生目錄宣告、先前 Git snapshot、事後 marker、entry hash、登錄 pin 與觀察界線 |
| [原生清單](../../../tests/fixtures/installer/observed-claude-superpowers-official.json)、[安裝回應](../../../tests/fixtures/installer/observed-claude-superpowers-install.json) | `7.0.0`、user scope、enabled，以及 install outcome；不是內容或功能的獨立驗收 |
| 既有案例 `evidence/installed-files.json`、`materialization-observation.json` | 238 檔的逐檔內容指紋、完整安裝樹、實際登錄 `gitCommitSha` |
| [host adapter](../../../runtime/agent_skills_installer/hosts.py) `_git_catalog` / `inspect_provider` | Claude 目前要求 `.git/config`、HEAD；無 Git 證據就拒絕 |
| [acceptance gate](../../../runtime/agent_skills_installer/providers.py)、[結果驗證](../../../runtime/agent_skills_installer/receipts.py) | 精確組合與完整 snapshot equality，不含受審閱的來源轉換政策 |
| [已核准設計](../../superpowers/specs/2026-11-10-superpowers-official-sources-design.md) | 保留既有 provider、完整 hash、分開批准、缺證據不寫入等約束 |

本機原始來源快照包含公開 marketplace、固定版本 manifest、Superpowers 安裝說明及 Codex 的原始碼片段；其中沒有解釋 Claude `.gcs-sha` 下載來源、驗證方式或生命週期的資料。隔離官方目錄內的 README 與 marketplace 也沒有相關說明。本 session 工具清單沒有暴露可呼叫的 Context7 工具。本輪依批准範圍不連網、不逆向 CLI 二進位，也沒有法律、價格或完整 API 文件查證；不作這些方面的相容性或安全保證。

## critical-research：先檢查反例

| 假設 | 反證／限制 | 判定 |
| --- | --- | --- |
| H1：Git metadata 會持續存在 | 實際案例先能讀 Git origin/HEAD，事後 `.git` 消失 | **Falsified，強證據**，限該案例 |
| H2：相同 marker 就足以證明來源 | marker 是可複製的 40-byte 字串，不含觀察者可獨立驗證的來源證明；不同來源也可帶相同字串 | **Unverified**；不能據此放行 |
| H3：命令 exit 0 表示能力驗收通過 | 兩個 mutation 都為 0，但事後來源驗證失敗 | **Falsified，強證據** |
| H4：記錄的 payload hash 等於已驗證的上游內容 | 重播證明 238 檔與先前觀察一致，不能證明它們獨立對應固定上游 tree | **僅部分支持**：保存一致，不是來源獨立驗證 |
| H5：一定是 install 命令觸發轉換 | 原觀察在 install 與三次盤點後才檢查目錄 | **Unknown**；不得歸因單一 vector |
| H6：所有來源規劃仍保留自有套件行為 | 實際純函式重播：兩個 host 的自有套件來源缺少時皆拋出 `AttributeError` | **Falsified，強證據**；需另修回歸 |

支持限定方案的資料：原生配置 URL、目錄位置、先前 Git HEAD、事後 marker 與所選 entry 都能對上；registry 的 payload commit 也與固定 pin 相同。這使「受限轉換」值得設計，卻不足以推導「任何既有封存目錄都可信」。兩個判斷的證據範圍不同，沒有互相抵銷。

## tech-feasibility：針對此安裝器的適用性

目標是維持來源可核對及既有套件隔離，同時容許已驗證官方目錄的特定原生轉換；不是建立通用封存套件管理器。

| 面向 | 需求與現有證據 | 結果 |
| --- | --- | --- |
| Technical fit | frozen model、純 gate、sealed action 可承接前後觀察；目前單一 snapshot equality 不容轉換 | **Conditional-Go**：須新增具階段區別的證據與純驗證 |
| Operational fit | 每次 mutation 最多一次；來源若在確認前變動仍需拒絕；cold-start archive 沒有前置 anchor | **有限適用**：先只設計同次 Git→archive，cold-start 維持 pending |
| Cost fit | 本輪只有本機分析，沒有新增外部服務／原生／模型呼叫；未估計之後下載、token 或供應商費率 | **本輪符合範圍**，不推論未來成本 |
| Legal/compliance fit | 未新增抓取、登入或發行；不讀個人 session/credentials | **未作法律／ToS 判定**；離線限制下沒有進行法律搜尋，不據此聲稱可發行 |
| Risk fit | marker-only / path-only / observed-hash-self-approval 會讓缺證據的來源被接受 | 這些做法是 **kill criteria**，不得採用 |
| Alternative fit | 可繼續停用；也可未來研究 cold-start archive 的原生來源證明 | 有較小保留方案，但不能宣稱完成自動安裝需求 |

Kill criteria 另包括：允許確認前轉換沿用舊批准、補寫原生 metadata、把未知 hash 當免檢、更新／降版既有 provider、以新規則干擾自有套件，以及沒有精確原生驗收紀錄就開放寫入。

## 方案取捨與建議

| 方案 | 做法 | 代價／最可能失敗情境 | 相對工作量 | 判定 |
| --- | --- | --- | --- | --- |
| A：同次操作的 Git→archive 驗證 | 使用當次可信 Git anchor，核對事後官方目錄、40-byte marker、entry/pin、完整 payload、native result 與受審閱政策 | 無前置 anchor 就不能用；若誤將跨次或確認前的轉換當作已批准，會放寬來源邊界 | 中；涉及 observations、policy、postcondition 及回歸案例 | **推薦進入設計；啟用仍有條件** |
| B：維持拒絕封存來源 | 保留目前 gate，顯示 pending 與原生指引，先修自有來源規劃回歸 | 無法完成此官方來源的自動安裝；若把 guide-only 寫成完成即形成誤導 | 小 | 可作保留方案，不是完整交付 |
| C：接受已存在的官方 archive | 為沒有當次 Git anchor 的封存來源建立獨立可信初始化及驗證途徑 | 本機目前缺少原生來源／驗證機制的 primary evidence；直接採用 marker 會把假資料當官方證據 | 大於 A，且需新證據 | **目前 No-Go**；不能由 A 順帶開放 |

`research-synthesis` 的整合建議是 A 作為**待審閱草案**，B 作為所有條件不足時的實際行為；C 保留未來獨立議題。critical-research 的反證要求排除 marker-only，tech-feasibility 則顯示既有型別／sealed action 可承接受限前後觀察；兩者不能被簡化成「封存來源已安全」。這是同 session、同一批證據的兩種分析，不是兩份獨立研究相互證明。

## 另發現的已重現回歸

[planning.py](../../../runtime/agent_skills_installer/planning.py) 第 92–100 行的自有來源分支，也封存了只對 Superpowers 初始化的 `readiness.snapshot`。當 `PluginSpec.provider is None`、所選 host 沒有 `tomwangowa` 來源時，`readiness` 為 `None`；Claude 與 Codex 都會在規劃來源新增時拋出例外。互動流程若拒絕來源準備後繼續預覽，也會碰到這條路徑。

本輪直接呼叫純 `make_plan` 重現兩個 host 的 `AttributeError: 'NoneType' object has no attribute 'snapshot'`，沒有原生命令或檔案寫入。這是前輪 provider source sealing 修改引入的回歸，**尚未修正**。舊 83-case suite 的通過不涵蓋這個情境；R4 不應交給同事作為已驗收安裝包。設計要求自有來源 action 不帶 Superpowers-only 證據，並列入必要回歸矩陣。

## VERIFIED / NOT VERIFIED

本輪重新核對了所有 238 個實際 payload 檔案及完整 tree hash，與原觀察相同；marker 是 **40 bytes、無換行**，其值對上舊 HEAD，marker 自身 SHA-256 是 `97ef0b1f529ab02020d5f8019fb6aa3f96a021f2a6a2ff5f2b615536871f3d41`。這只驗證現存證據保存一致。

仍未驗證：轉換的單一觸發 vector、初始 `.gcs-sha` 是否缺少、Claude archive 的可信原生來源契約、完整 pin tree 的獨立比對、新設計正常／失敗案例、未修改候選包安裝及模型行為。未新增 acceptance record 或接受已觀察 hash 為產品預期值。

本機重播檔案位於 `.superpowers/sdd/2026-11-10-superpowers-official-sources/`：`archive-investigation-replay.json`、`archive-investigation-own-source-repro.json`。一次分析命令誤匯入不存在的 dummy 模組，於任何觀察／外部操作前失敗；修正後的重播才產生上述結果，沒有重試外部服務。
