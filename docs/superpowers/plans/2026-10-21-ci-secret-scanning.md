# Pull request secret scanning in CI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (recommended for this sequential two-task change) or superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** 在既有必要 PR job 中，以 Gitleaks 和 TruffleHog 掃描 PR 新增 commit，並在命中或掃描無法完成時阻擋合併。

**Architecture:** Workflow 保持 checkout 在 GitHub merge ref，PR 事件另外 fetch 並驗證 head SHA，下載固定 ARM64 發行檔並檢查 SHA-256。Python 3.12 標準函式庫 helper 驗證 merge-base..head 範圍、執行兩個 CLI、解析暫存報告並輸出安全摘要。

**Tech Stack:** GitHub Actions YAML、Python 3.12 標準函式庫、Git、Gitleaks 8.30.1、TruffleHog 3.97.4、curl、shasum、tar。

**Spec:** docs/superpowers/specs/2026-10-21-ci-secret-scanning-design.md

## Global Constraints

- 掃描只在 pull_request 執行，放進既有必要 job tests-and-plugin-integrity；保留 job 名稱、ruleset 和 contents: read 權限。
- Checkout 保持 GitHub 預設 PR merge ref；PR 的 fetch-depth 為 0，其他事件為 1；既有測試仍在掃描通過後執行。
- 使用事件中的 base/head SHA；先驗證 PR head ref 正好解析為 head SHA，再掃描非空的 merge-base..head 範圍。
- fetch-depth 0 會下載完整 Git 歷史；掃描器只讀已驗證的 PR 範圍，下載耗時尚未量測。
- Runner 為 macos-26 ARM64；架構不符就失敗。
- 固定 Gitleaks 8.30.1，檔案 gitleaks_8.30.1_darwin_arm64.tar.gz，SHA-256 b40ab0ae55c505963e365f271a8d3846efbc170aa17f2607f13df610a9aeb6a5。
- 固定 TruffleHog 3.97.4，檔案 trufflehog_3.97.4_darwin_arm64.tar.gz，SHA-256 57e2a41c1e196cf96cae49ca2151f5e9207be2f5c41349b5ea49cb5dcfc606b7。
- TruffleHog 使用 --no-verification，並掃描 verified、unverified、unknown 結果；命中仍失敗。
- 下載、雜湊／版本檢查、範圍驗證、命令執行或報告解析失敗都 fail closed。
- 原始 stdout、stderr、候選值與完整報告不得輸出到 Actions 日誌；不得上傳報告 artifact。只輸出白名單摘要並先移除候選值。
- 不新增本機 hook、通用忽略清單、額外 required job 或 ruleset；不使用 pull_request_target。
- 威脅範圍是攔截一般意外提交；PR 可修改其執行中的 workflow，不能防範刻意停用掃描。
- 本計畫不新增測試套件或測試樣本；不得自行提交變更，提交前須取得使用者明確核准。

## Review Focus

以下失敗情境沒有專用自動化測試覆蓋；實作須逐項檢視 fail-closed 行為，並在 PR 的既有必要 job 核對整合結果：

1. **Task 1 — 空範圍或缺失 Git object：** base、head、merge-base 無效，或 merge-base..head 沒有 commit 時，必須在呼叫掃描器前失敗。
2. **Task 1 — 非零掃描器 exit code：** 命中造成非零結果時仍解析報告並產生安全摘要；其他非零結果也失敗。
3. **Task 1 — 空白或格式錯誤報告：** Gitleaks 空結果須是有效 JSON；TruffleHog 無命中可為空 JSON Lines；其他無法解析或不符固定版本欄位結構的結果都失敗。
4. **Task 1 — 候選值或惡意路徑字元：** 候選值不得出現在摘要；路徑中的控制字元必須經 JSON 編碼，不能拆成額外日誌行。
5. **Task 2 — PR head ref 與架構不符：** fetched head SHA 不同或 runner 不是 ARM64 時立即失敗，不得略過掃描繼續執行測試。

---

### Task 1: Create the safe PR scanning helper

**Files:**
- Create: scripts/scan_pr_secrets.py
- Test: none in this plan; do not add test files unless the user asks.

**Interfaces:**
- Required environment variables: BASE_SHA, HEAD_SHA, GITLEAKS_BIN, TRUFFLEHOG_BIN, and RUNNER_TEMP.
- resolve_scan_range(base_sha: str, head_sha: str) -> tuple[str, str] returns the validated merge-base SHA and merge-base..head revision range. It rejects missing commits, invalid ancestry, Git errors, and a zero commit count.
- Finding contains tool: str, detector: str, file: str, line: int | None, and commit: str | None.
- ScanReport contains findings: tuple[Finding, ...] and candidate_values: tuple[str, ...] for scrubbing summary metadata.
- parse_gitleaks_report(path: Path) -> ScanReport parses one Gitleaks JSON document.
- parse_trufflehog_report(path: Path) -> ScanReport parses TruffleHog JSON Lines.
- main() -> int returns zero only when both scanners complete successfully with no findings; every finding or processing error returns nonzero.

- [x] **Step 1: Add the report data types and range validation.** Implement Finding, ScanReport, and resolve_scan_range using list-form subprocess.run calls with shell=False. Validate that both inputs resolve to commits, calculate git merge-base BASE_SHA HEAD_SHA, confirm the merge-base is an ancestor of head, and require git rev-list --count MERGE_BASE..HEAD_SHA to be greater than zero. Do not print Git stderr.

- [x] **Step 2: Add strict report parsers.** Parse Gitleaks as a single JSON document and TruffleHog one JSON object per nonempty line. Parse a valid empty Gitleaks result or empty TruffleHog JSON Lines as no findings; main() may treat them as clean only when the corresponding scanner exit code is zero. Require each finding to contain the expected pinned-version detector and Git metadata; normalize an absent or zero line number to `null`, while rejecting negative or non-integer line numbers. Unexpected shapes or malformed JSON raise a sanitized parse failure. Collect Gitleaks Secret/Match and TruffleHog Raw/RawV2/SecretParts values for later scrubbing; never include these or other raw report fields in the summary.

- [x] **Step 3: Implement scanner execution and result aggregation in main() -> int.** Read the required environment variables, validate binary paths, create report and capture files under a mode-0700 TemporaryDirectory inside RUNNER_TEMP, and execute both commands with subprocess.run(check=False, shell=False). Pass Gitleaks git, --log-opts MERGE_BASE..HEAD_SHA, --report-format json, and --report-path. Do not use Gitleaks --redact: it hides Secret/Match before the helper can scrub metadata such as File. Pass TruffleHog git file://., --since-commit MERGE_BASE, --branch HEAD_SHA, --json, --no-verification, --results=verified,unverified,unknown, --fail, and --fail-on-scan-errors. Redirect all stdout/stderr to files in that temporary directory; parse TruffleHog's stdout JSON Lines and Gitleaks's report file. Still parse reports when a finding produces a nonzero exit code; run the second scanner even if the first reports findings. TemporaryDirectory removes the reports and captured output after parsing.

- [x] **Step 4: Emit only a safe summary and aggregate status.** Serialize only the whitelisted finding fields as JSON Lines. Remove every collected candidate string from all summary text before serialization. For command, environment, and parse failures, emit only tool name, error category, and exit code; never print raw exception text, stdout, stderr, or reports. Return nonzero if either scanner has findings, a nonzero exit status, an invalid report, or any range/runtime error.

- [x] **Step 5: Run a syntax check and inspect the new helper.** Run python3 -m py_compile scripts/scan_pr_secrets.py and git diff --check. Expected: exit status 0 and no whitespace errors. Do not run the repository test suite as part of this plan.

---

### Task 2: Wire the pinned scanners into the required PR job

**Files:**
- Modify: .github/workflows/tests-and-plugin-integrity.yml
- Consumes: scripts/scan_pr_secrets.py and the environment interface from Task 1.

- [x] **Step 1: Make checkout depth conditional without changing its ref.** Keep actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 and default PR merge-ref behavior. Set fetch-depth to the expression ${{ github.event_name == 'pull_request' && '0' || '1' }}; use string values so 0 is not treated as false.

- [x] **Step 2: Fetch and verify the PR head on PR events only.** After checkout, add a step guarded by github.event_name == 'pull_request'. Pass the PR number and github.event.pull_request.head.sha through environment variables. Fetch refs/pull/<number>/head into a dedicated local ref and compare its resolved commit SHA to the event head SHA. On mismatch or fetch failure, stop the job. Do not interpolate the PR branch name or title into shell code.

- [x] **Step 3: Confirm the runner architecture and download both ARM64 releases.** Add a PR-only step after setup-python and before setup-node. Assert uname -m is arm64. Download https://github.com/gitleaks/gitleaks/releases/download/v8.30.1/gitleaks_8.30.1_darwin_arm64.tar.gz and https://github.com/trufflesecurity/trufflehog/releases/download/v3.97.4/trufflehog_3.97.4_darwin_arm64.tar.gz into $RUNNER_TEMP. Any failed command stops the job.

- [x] **Step 4: Verify release hashes, extract binaries, and check versions.** Compare each archive's SHA-256 to the fixed value in Global Constraints using shasum -a 256 --check before extraction. Extract only gitleaks and trufflehog into $RUNNER_TEMP/bin. Require gitleaks --version output to identify 8.30.1 and trufflehog --version output to identify 3.97.4. Stop on a mismatch.

- [x] **Step 5: Invoke the helper before dependency installation and tests.** Add a PR-only step before Node setup and npm ci. Set BASE_SHA and HEAD_SHA from the pull request event, and set GITLEAKS_BIN/TRUFFLEHOG_BIN to the extracted binaries. Invoke python3 scripts/scan_pr_secrets.py. Do not use continue-on-error. On a clean scan, the existing dependency setup and tests continue against the merge ref.

- [x] **Step 6: Check the final workflow diff.** Run git diff --check and inspect the workflow to confirm scanner steps are PR-only, the job name and permissions are unchanged, and no report path is uploaded or printed. The required PR job is the integration evidence; expected result is both scanners pass without raw report output, followed by the existing tests. Do not commit unless the user separately approves.

## Execution Verification Limits

- A live GitHub Actions PR run is required to verify the macOS runner, asset downloads, ref fetch, actual scanner outputs, and the existing job's end-to-end behavior.
- The automated report-parser failure branches and synthetic finding behavior are not independently tested in this plan; if that coverage is required, ask the user before adding or running tests.
- The TruffleHog AGPL-3.0 policy question and Gitleaks 8.30.1 source provenance remain the risks recorded in the spec.
