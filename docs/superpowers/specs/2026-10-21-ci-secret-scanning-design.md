---
title: Pull request secret scanning in CI
date: 2026-10-21
status: approved
---

# Pull request secret scanning in CI

## 1. Goal

在 PR 合併前，用 Gitleaks 和 TruffleHog 掃描 PR 新增的 commit。任一工具找到可能的憑證，或安裝、範圍計算、掃描發生錯誤，都讓既有必要檢查失敗。

此設計針對一般意外提交。GitHub 的 `pull_request` 工作流程會使用 PR 合併結果中的工作流程內容，因此 PR 可以修改自己的掃描步驟。使用者已接受這項限制；本設計不保證惡意 PR 無法停用掃描。

## 2. Confirmed decisions

- 只在 CI 掃描，不新增本機 hook。
- 只掃 PR 新增的 commit，不掃完整 Git 歷史。
- 掃描步驟只在 `pull_request` 執行；不在 `push` 到 `main` 或 `workflow_dispatch` 執行。
- 將掃描器加進既有必要 job `tests-and-plugin-integrity`，不改 job 名稱或 ruleset。
- 任一工具命中或掃描流程出錯都讓必要 job 失敗。
- 固定 Gitleaks `8.30.1` 和 TruffleHog `3.97.4`，人工升級。
- Gitleaks 8.30.1 使用固定的官方 macOS ARM64 發行檔 SHA-256；TruffleHog 也固定相同平台發行檔的 SHA-256。
- 停用 TruffleHog 的線上憑證驗證；未驗證命中仍會讓 CI 失敗。
- 完整候選值不輸出到 Actions 日誌，不上傳掃描報告。
- 初始版本不加通用忽略清單。確認誤報後，只提出範圍最小且經審核的例外。
- 保留 Gitleaks 8.30.1 的 tag 來源風險說明。
- 將 TruffleHog AGPL-3.0 的組織政策適用性列為未查證事項，不自行作法律判斷。

## 3. Verified repository and tool facts

- 工作流程是 `.github/workflows/tests-and-plugin-integrity.yml`，目前在 `macos-26` 執行，觸發條件含 `pull_request`、`push` 到 `main` 和 `workflow_dispatch`。必要狀態名稱為 `tests-and-plugin-integrity`。
- 目前 `actions/checkout` 固定在 v7.0.1，預設 checkout 為淺層歷史；`pull_request` 預設使用 GitHub 的 merge ref。掃描器要指定 PR head SHA，但不必改變現有測試所用的 merge checkout。
- GitHub 目前將 `macos-26` 列為 ARM64 標準 runner。掃描器使用 `darwin_arm64` 發行檔；若執行架構不符就失敗。
- 在本次檢視的 repo 快照中，Git 歷史約 458 個 commit、追蹤檔案約 8,843 個。`fetch-depth: 0` 會取回完整歷史以便計算 merge-base，但送給掃描器的範圍仍限定為 `merge-base..head`。歷史下載時間尚未實測。
- Gitleaks 8.30.1 官方發行檔 SHA-256：`b40ab0ae55c505963e365f271a8d3846efbc170aa17f2607f13df610a9aeb6a5`，檔案為 `gitleaks_8.30.1_darwin_arm64.tar.gz`。
- TruffleHog 3.97.4 官方發行檔 SHA-256：`57e2a41c1e196cf96cae49ca2151f5e9207be2f5c41349b5ea49cb5dcfc606b7`，檔案為 `trufflehog_3.97.4_darwin_arm64.tar.gz`。
- Gitleaks 8.30.1 的 tag 指向不在 `master` 歷史上的 commit；維護者在 issue 中承認 release 出錯。另一個聲稱該版本完全偵測不到憑證的 issue，後來確認測試 token 命中 stopword，並已關閉。這不足以證明二進位檔遭竄改或掃描器失效，但來源脈絡仍需記錄。固定 SHA-256 可鎖定預期檔案內容，無法補上上游來源鏈的缺口。
- TruffleHog 3.97.4 JSON 輸出包含 `Raw` 等原始資料欄位。輸出必須先存到 runner 暫存區，再以欄位白名單產生摘要；不得直接列印或上傳原始 JSON。
- TruffleHog 3.97.4 採 AGPL-3.0。檢視的 repo 快照中沒有根目錄授權檔或第三方工具政策，政策適用性尚未確認。

## 4. Approaches considered

### A. 直接安裝固定版本 CLI，掃描明確 commit 範圍（選定）

下載官方 macOS ARM64 二進位檔，以工作流程內固定的 SHA-256 驗證，再呼叫兩個 CLI 掃描 `merge-base..head`。這沿用現有 macOS job，能直接控制版本、範圍、離線驗證和輸出欄位。

代價是每次 PR 都要下載工具和完整 Git 歷史，並維護範圍驗證與安全摘要。最可能的失敗是 merge-base 算錯，或 Gitleaks 收到空範圍後仍回傳成功；流程會驗證祖先關係、預先確認範圍至少含一個 commit，並要求掃描命令成功完成。

### B. 使用 TruffleHog 官方 GitHub Action

可少寫一部分安裝和參數處理，但 v3.97.4 Action 的 composite script 會執行 `docker run`。目前 `macos-26` runner 的官方軟體清單沒有列出 Docker；要另備 Docker runtime 或改用 Linux runner，會擴大本次範圍。Action 的事件範圍處理也直接使用 event base/head，沒有本設計的 merge-base 防護。主要風險是為了套用 Action 而改動 runner 後，範圍或報告處理仍不符合本 repo 的需求。

### C. 自行解析 PR diff

可避免完整 Git 歷史下載，也能只看最後合併後的檔案差異。代價是自己處理多行內容、刪除後又加入的值、重新命名、二進位檔與 patch 格式；最可能的失敗是 diff 解析漏掃。為避免自行重作兩個掃描器的 Git 邏輯，不採用此方案。

## 5. Selected design

### Workflow placement

保留單一 workflow 和單一必要 job。將掃描步驟加在 `.github/workflows/tests-and-plugin-integrity.yml` 的 `tests-and-plugin-integrity` job，放在既有 `setup-python` 後、Node 相依套件安裝和測試前，並以 `github.event_name == 'pull_request'` 限定執行。這樣命中時能在昂貴的 npm 安裝和測試前結束 job；掃描通過時，既有測試仍使用預設 merge ref，維持原本驗證合併結果的行為。不新增 status context、不改 ruleset，也不使用 `pull_request_target`。

### Component boundary

Workflow 負責 PR 條件、checkout 歷史深度、取得固定發行檔、SHA-256 驗證與呼叫掃描器。新增 `scripts/scan_pr_secrets.py`，集中驗證 base/head/merge-base、執行兩個 CLI、捕捉輸出、產生安全摘要和回傳最終狀態。它使用現有 job 已安裝的 Python 3.12 標準函式庫，不新增套件。

### Checkout and range

PR 事件將既有 checkout 的 `fetch-depth` 設為 `0`，其他事件維持 `1`；若用 GitHub Actions expression 設定單一 input，使用字串 `'0'`／`'1'`，避免數值 `0` 被 `&&`／`||` 表達式當成 false。checkout 繼續使用預設 merge ref，讓既有測試仍驗證合併結果。PR 專用步驟再把 `refs/pull/<number>/head` 完整抓進同一個 Git object database，並確認它解析到事件中的 head SHA。用事件中的 base SHA 與 head SHA 計算：

1. `MERGE_BASE = git merge-base BASE_SHA HEAD_SHA`。
2. 驗證兩端 commit 和 merge-base 存在，且 merge-base 是 head 的祖先。
3. 用 `git rev-list --count "$MERGE_BASE..$HEAD_SHA"` 驗證範圍至少含一個 commit；空範圍或 Git 指令錯誤都失敗。
4. 將同一個已驗證範圍傳給兩個掃描器；兩個工具都以 PR head SHA 為範圍終點。

SHA 透過環境變數傳給 shell，不把 PR 分支名稱或標題插入指令。使用 merge-base 可避免 TruffleHog 收到非祖先 base SHA 時退回掃描更長歷史的風險。

### Tool installation and scan behavior

1. 確認 runner 為 ARM64，下載上述固定版本和發行檔，先比對工作流程內的 SHA-256，再解壓到 `$RUNNER_TEMP`。下載、驗證或解壓失敗即停止。
2. Gitleaks 使用 `git` 模式和 `--log-opts "$MERGE_BASE..$HEAD_SHA"`，設定 `--report-format json`，並將報告寫進權限為 `0700` 的暫存目錄。刻意不設定 `--redact`：v8.30.1 會先遮蔽 `Secret`／`Match`，卻保留 `File`；helper 需要原始候選值才能安全遮蔽檔案路徑等摘要欄位。範圍預檢須確認至少含一個 commit；掃描命令失敗或報告缺失／無法解析都視為失敗。
3. TruffleHog 使用 Git 掃描模式，以 `--since-commit "$MERGE_BASE"`、`--branch "$HEAD_SHA"` 限定範圍，明確設定 `--json`、`--no-verification`，並包含 `verified`、`unverified`、`unknown` 結果。啟用 `--fail` 與 `--fail-on-scan-errors`；JSON 輸出寫入 `$RUNNER_TEMP`。
4. Helper 記錄掃描器的 exit code 後，仍解析暫存報告；命中所用的非零 exit code 不得中斷安全摘要產生。任何一方找到結果或命令回報錯誤，都使 job 失敗。不得設定 `continue-on-error`。

### Safe output

兩個工具的完整輸出都先寫到 `$RUNNER_TEMP` 下權限為 `0700` 的暫存目錄。Helper 將 Gitleaks JSON 報告當成單一 JSON 文件解析，逐行解析 TruffleHog JSON Lines。無命中時只接受 Gitleaks 的有效空結果及 TruffleHog 成功退出且無 JSON Lines；每筆命中都必須符合該固定版本的預期欄位結構，否則 fail closed。摘要只保留規則或偵測器名稱、檔案、行號、commit 和命中數；Python JSON filter 只輸出這些白名單欄位，並 JSON-encode 每筆資料，避免 PR 路徑的控制字元變成額外日誌行。摘要產生前，先從報告讀出候選值欄位（Gitleaks 的 `Secret`／`Match`，TruffleHog 的 `Raw`／`RawV2` 等），並從所有摘要文字中移除這些值。原始候選值和原始報告只留在暫存檔中供遮蔽處理，不列印、不上傳 artifact；TemporaryDirectory 在 helper 結束時移除檔案。這也避免只遮蔽 Gitleaks 的 `Secret`／`Match` 卻將含候選值的 `File` 路徑寫進摘要。

誤報仍會先阻擋合併。若之後需要例外，審查者應確認規則和最小路徑範圍，避免加入整類憑證的忽略設定。

## 6. Failure behavior

以下任一情況都讓必要 job 失敗：

- 工具下載、版本檢查、SHA-256 驗證或解壓失敗。
- runner 架構不支援。
- base/head/merge-base 無效、祖先驗證失敗，或 PR 範圍為空。
- 預檢後的掃描範圍為空、Gitleaks 報告缺失／無法解析，或任一掃描命令失敗。
- 任一掃描器找到結果。
- 任一掃描器、摘要解析或範圍讀取發生錯誤。

掃描器原始輸出可能含候選值，所以失敗摘要只顯示工具名稱、錯誤類型或 exit code，以及安全欄位；不列印原始 stdout/stderr，不上傳報告。

## 7. Feasibility and risks

**判斷：有條件採用。** 直接呼叫 CLI 與現有 macOS ARM64 runner 相容；官方 CLI 支援指定 Git 範圍，並能在命中時回傳失敗。操作成本是下載兩個工具和完整 Git 歷史，實際增加時間尚未測量。GitHub 文件目前將公開 repo 的標準託管 runner 列為免費使用；成本不包含維護時間。

條件和已接受風險：

- **Gitleaks 來源脈絡：** 保留 8.30.1 並固定發行檔 SHA-256，但仍信任該官方發行檔的來源。
- **TruffleHog 授權：** AGPL-3.0 是否符合 repo 所屬組織政策尚未確認；本設計不作法律結論。
- **PR 繞過：** PR 可修改其執行中的 workflow；目前承諾範圍是攔截一般意外提交，不抵抗刻意停用掃描。
- **完整歷史下載：** 掃描器只掃 PR 範圍，但 checkout 會下載全歷史；repo 增長可能讓 job 變慢。
- **雜湊維護：** 升級時必須一起更新版本、官方 asset 名稱和固定 SHA-256。

若授權政策不允許 AGPL 工具，或威脅模型要求 PR 無法修改掃描邏輯，這份設計需重新選型。若工具發行檔 hash 不符，工作流程 fail closed，不以跳過驗證處理。

## 8. Out of scope

- 掃描 `main` push、`workflow_dispatch` 或整段 repository history。
- 本機 hook、排程式歷史盤點、額外 required job 或 ruleset 修改。
- TruffleHog 線上憑證驗證、原始報告 artifact、通用 allowlist。
- 將 CI 掃描宣稱為防範惡意 PR 的安全邊界。
- 自動追蹤最新版或自動更新掃描器。

## 9. Acceptance criteria

- 掃描步驟只在 PR 執行，仍屬既有 `tests-and-plugin-integrity` 必要 job；既有測試仍對 merge ref 執行。
- Gitleaks 與 TruffleHog 都只收到已驗證的 `merge-base..head` 範圍；取回完整歷史不等於掃描完整歷史。
- 兩個版本、ARM64 發行檔和 SHA-256 固定；任何取得或驗證失敗都阻擋 job。
- 任一掃描器命中、無法確認非空掃描範圍、報告缺失／無法解析或執行錯誤都阻擋合併。
- 日誌只輸出安全摘要，不包含候選憑證值；沒有原始報告 artifact。
- 對 TruffleHog 的線上驗證維持停用，未驗證命中仍會失敗。
- 使用者核准本書面規格後，才撰寫 implementation plan。

實作後由既有 PR 必要 job 驗證 macOS runner、下載與雜湊檢查、範圍計算、兩個掃描器以及安全摘要。既有測試照常執行；本設計不另加含憑證值的測試樣本，也不新增測試套件。

## 10. References

- [GitHub Actions: events that trigger workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows) — PR 的 merge ref 和 head SHA。
- [actions/checkout v7.0.1 README](https://github.com/actions/checkout/blob/v7.0.1/README.md?plain=1) — `fetch-depth: 0` 和 PR head checkout。
- [GitHub-hosted runners reference](https://docs.github.com/en/actions/reference/runners/github-hosted-runners) — `macos-26` 架構與公開 repo 的 runner 費用。
- [macos-26 runner image](https://github.com/actions/runner-images/blob/main/images/macos/macos-26-Readme.md) — runner 軟體清單，用來確認文件是否列出 Docker。
- [Gitleaks v8.30.1 `cmd/git.go`](https://github.com/gitleaks/gitleaks/blob/v8.30.1/cmd/git.go) 和 [root command](https://github.com/gitleaks/gitleaks/blob/v8.30.1/cmd/root.go) — Git 範圍與遮蔽參數。
- [Gitleaks v8.30.1 release checksums](https://github.com/gitleaks/gitleaks/releases/download/v8.30.1/gitleaks_8.30.1_checksums.txt) — 選定的 ARM64 發行檔雜湊。
- [Gitleaks issue #2086](https://github.com/gitleaks/gitleaks/issues/2086) — tag 不在主線歷史，以及維護者承認發行出錯。
- [Gitleaks issue #2170](https://github.com/gitleaks/gitleaks/issues/2170) — 後來確認測試值命中停用字、並已關閉的回報。
- [Gitleaks issue #2129](https://github.com/gitleaks/gitleaks/issues/2129) — 零 commit 掃描可能回報成功的問題。
- [TruffleHog v3.97.4 README](https://github.com/trufflesecurity/trufflehog/blob/v3.97.4/README.md) 和 [engine 原始碼](https://github.com/trufflesecurity/trufflehog/blob/v3.97.4/pkg/engine/engine.go) — Git 範圍、停用驗證和命中失敗行為。
- [TruffleHog v3.97.4 JSON 輸出](https://github.com/trufflesecurity/trufflehog/blob/v3.97.4/pkg/output/json.go) — 不可寫入日誌的原始資料欄位。
- [TruffleHog v3.97.4 發行檔雜湊](https://github.com/trufflesecurity/trufflehog/releases/download/v3.97.4/trufflehog_3.97.4_checksums.txt)、[Action 原始碼](https://github.com/trufflesecurity/trufflehog/blob/v3.97.4/action.yml) 和 [授權](https://github.com/trufflesecurity/trufflehog/blob/v3.97.4/LICENSE)。
- [TruffleHog issue #3220](https://github.com/trufflesecurity/trufflehog/issues/3220) — `--since-commit` 不屬於 head 歷史時的掃描範圍風險。
- [GitHub Actions 自訂 Action 文件](https://docs.github.com/en/actions/concepts/workflows-and-actions/custom-actions) — Docker container action 需要 Linux runner。
