# session-start (PR-1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增 user-level `session-start` skill（讀回 handoff、轉手給 repo-local 版），登記進 catalog，並打包進 `repo-workflow`。

**Architecture:** `session-start/scripts/handoffs.py` 是單檔標準函式庫 CLI，有 `check`、`list`、`mark-resumed`、`delegate` 四個子指令，輸出都是 JSON；`session-start/SKILL.md` 負責編排與對話。測試放頂層 `tests/`，用 subprocess 跑 CLI，搭配暫存 git repo。

**Tech Stack:** Python 3.12 標準函式庫、git CLI、`unittest`。

**Spec:** `docs/superpowers/specs/2026-10-18-session-start-task-bootstrap-design.md`（本計畫只涵蓋 D1、D2、D4–D8、D14–D18 中屬於 `session-start` 的部分；`task-bootstrap` 是 PR-2）。

## Global Constraints

- 只用 Python 標準函式庫與 git CLI；subprocess 一律傳參數陣列，不用 `shell=True`。
- handoff 內容是不可信資料：除了白名單 assertion，不執行、不評估其中任何文字。
- clean-room（D15）：不讀、不複製任何 repo-local 參考實作的程式碼；提交的檔案不寫那些 repo 的名稱或內部細節。
- `repo-workflow` 版號維持 `0.1.0`（D16）。
- 程式碼註解用英文，只解釋「為什麼」。
- 測試從 repo 根目錄跑：`python3 -m unittest tests.test_session_start_handoffs -v`。新 worktree 先在 `skills-query-server/` 跑一次 `npm ci`，否則 `tests/test_build_plugins.py` 會出現與本計畫無關的 error。
- 每個 Commit 步驟都要先取得 Tom 同意；commit 前依 `completion-gate` 判斷 L0／L1／L2，L1／L2 用 `code-review-claude`。訊息遵守 Conventional Commits，結尾加 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`。
- 第一個 commit 是 spec 加本計畫：`docs(specs): add session-start and task-bootstrap design`。

## Review Focus

1. 測試環境吃到 Tom 的全域 git 設定（commit 簽章、hooks、全域 gitignore 的 `**/.claude/handoffs/`）：fixture 必須隔離，否則換一台機器結果就不同。→ Task 1 的 fixture 與 `test_fixture_isolated_from_global_git_config`。
2. handoff 檔是 CRLF 換行或開頭有 BOM：預期能正常解析，不當成「不是 handoff」。→ Task 1 `test_parse_crlf_and_bom`。
3. `created` 沒有時區、或用 `Z` 結尾：預期能比較時間，不因為 aware／naive 混用而 TypeError。→ Task 2 `test_created_formats_compare`。
4. 檔名含空白或中日韓文字：預期照常列出。→ Task 2 `test_unicode_and_space_filenames`。
5. PATH 裡沒有 git：預期退回「只讀 cwd」，不崩潰。→ Task 2 `test_git_unavailable_falls_back_to_cwd`。

---

### Task 1: frontmatter 解析、assertion 與 `check`

**Files:**
- Create: `session-start/scripts/handoffs.py`
- Create: `tests/test_session_start_handoffs.py`

**Interfaces:**
- Produces（`handoffs.py`）：
  - `ASSERTION_KINDS: tuple[str, ...] = ("expect_head", "branch_is", "file_exists", "worktree_clean")`
  - `@dataclass class ParsedHandoff: kind: str  # "ok" | "malformed" | "not_handoff"`；`fields: dict[str, str]`；`assertions: list[dict[str, str]]`；`body: str`；`body_offset: int`（body 在原始 bytes 中的起點）
  - `parse_handoff(raw: bytes) -> ParsedHandoff`
  - `split_sections(body: str) -> dict[str, str]`：以 `## ` 標題為 key（去掉 `## `），值是到下一個 `## ` 之前的文字
  - `run_assertion(item: dict[str, str]) -> dict[str, str]`：回傳 `{"kind", "result", "detail"}`，`result` 是 `"pass" | "fail" | "unverified"`
  - `git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str] | None`：git 不存在時回傳 `None`
  - `main(argv: list[str] | None = None) -> int`，CLI `check PATH [--cwd DIR]`
- Produces（測試檔，後續 Task 共用）：`GIT_ENV`（`GIT_CONFIG_GLOBAL=os.devnull`、`GIT_CONFIG_NOSYSTEM=1`、固定 author／committer）、`make_repo(path: Path) -> Path`（`git init -b main`，含一個初始 commit，並把 `.claude/handoffs/` 寫進 `.git/info/exclude`）、`write_handoff(dir: Path, name: str, *, frontmatter: str, body: str = "## 任務\nx\n") -> Path`、`run_cli(script: Path, *args: str, cwd: Path, env: dict | None = None) -> tuple[int, dict]`。

解析規則：檔案開頭（去掉 BOM、`\r\n` 視同 `\n`）必須是 `---` 行，直到下一個 `---` 行為 frontmatter。支援 `key: scalar`（去掉引號、去掉前面有空白的 ` #` 註解），以及 `assertions:` 底下 `  - k: v` 開頭、`    k: v` 延續的 mapping 清單。沒有 frontmatter 或沒有 `status` 是 `not_handoff`；有 `status` 但出現其他形狀（巢狀 mapping、清單值等）是 `malformed`。

assertion 規則：`repo`／`path` 必須是絕對路徑，否則 `unverified`。`repo` 不是 git repo 也是 `unverified`。`expect_head`：`rev-parse HEAD` 以 `value` 開頭才 `pass`。`branch_is`：`symbolic-ref --short -q HEAD` 等於 `value`。`file_exists`：`Path.exists()`。`worktree_clean`：`status --porcelain` 輸出為空。不認得的 kind 是 `unverified`。

`check` 輸出：`{"path", "kind", "status", "task", "fields", "assertions", "sections", "sha256", "already_resumed", "worktree_matches_cwd"}`。`malformed` 時 `assertions` 固定是 `[]`。`not_handoff` 回傳 exit 2 與 `{"error": "not_handoff"}`；檔案不存在回傳 exit 2 與 `{"error": "not_found"}`。`worktree_matches_cwd` 比較 frontmatter `worktree` 和 cwd 所在 git 根目錄（非 git 時用 cwd）的 realpath。

- [ ] **Step 1: 寫失敗的測試**

`class ParseTests` 與 `class CheckTests`，測試與斷言：
- `test_fixture_isolated_from_global_git_config`：`git config --get core.excludesFile`（帶 `GIT_ENV`，在 fixture repo 中）回傳碼不是 0。
- `test_parse_template_shape`：frontmatter 有 `status: in-progress   # a | b` 和兩個 assertion → `kind == "ok"`、`fields["status"] == "in-progress"`、`len(assertions) == 2`、`assertions[0] == {"kind": "expect_head", "repo": "/r", "value": "abc1234"}`。
- `test_parse_crlf_and_bom`：同一份內容改成 `b"\xef\xbb\xbf"` 開頭並使用 `\r\n` → `kind == "ok"`，fields 與上一個測試相同。
- `test_parse_without_frontmatter_is_not_handoff`、`test_parse_without_status_is_not_handoff`：`kind == "not_handoff"`。
- `test_parse_nested_mapping_is_malformed`：`status: blocked\nextra:\n  child: 1` → `kind == "malformed"`。
- `test_split_sections`：`"## 任務\na\n## 下一步\nb\n"` → `{"任務": "a", "下一步": "b"}`（值 strip 後比較）。
- `test_expect_head_pass_and_fail`：用 HEAD 前 7 碼 → `pass`；`"0000000"` → `fail`。
- `test_branch_is_pass_and_fail`、`test_file_exists_pass_and_fail`。
- `test_worktree_clean_pass_and_fail`：新增未追蹤檔之後 → `fail`。
- `test_unknown_kind_is_unverified`、`test_relative_path_is_unverified`、`test_non_git_repo_is_unverified`。
- `test_check_malformed_runs_no_assertions`：`kind == "malformed"`、`assertions == []`、`"任務" in sections`。
- `test_check_not_handoff_exits_2`：`(2, {"error": "not_handoff"})`。
- `test_check_reports_sha256_and_resumed`：`sha256 == hashlib.sha256(path.read_bytes()).hexdigest()`；`status: resumed` 時 `already_resumed is True`。
- `test_check_worktree_mismatch`：frontmatter `worktree` 是另一個目錄 → `worktree_matches_cwd is False`；等於 fixture repo → `True`。
- `test_whitelist_matches_handoff_skill`：在 `handoff/SKILL.md` 中，從含有 `Assertion 白名單` 的那一行開始，收集形如 ``| `name` |`` 的表格列，直到表格結束；集合必須等於 `set(ASSERTION_KINDS)`（用 `importlib.util.spec_from_file_location` 載入 `handoffs.py`）。

- [ ] **Step 2: 執行測試，確認失敗**

Run: `python3 -m unittest tests.test_session_start_handoffs -v`
Expected: FAIL／ERROR，原因是 `session-start/scripts/handoffs.py` 不存在。

- [ ] **Step 3: 在 `session-start/scripts/handoffs.py` 實作上面 Interfaces 列出的內容**

git 呼叫一律 `git -C <repo> …`，並帶上 timeout；`FileNotFoundError` 時回傳 `None`。JSON 用 `ensure_ascii=False` 輸出到 stdout。

- [ ] **Step 4: 執行測試，確認通過**

Run: `python3 -m unittest tests.test_session_start_handoffs -v`
Expected: 全部 PASS。

- [ ] **Step 5: Commit（先問 Tom）**

```bash
git add session-start/scripts/handoffs.py tests/test_session_start_handoffs.py
git commit -m "feat(session-start): parse handoffs and check whitelisted assertions"
```

### Task 2: `list`

**Files:**
- Modify: `session-start/scripts/handoffs.py`
- Modify: `tests/test_session_start_handoffs.py`

**Interfaces:**
- Consumes: Task 1 的 `parse_handoff`、`git`、測試 fixture。
- Produces:
  - `@dataclass class Location: handoffs_dir: Path; worktree: Path; branch: str | None; current: bool`
  - `discover_locations(cwd: Path) -> tuple[str, list[Location]]`：回傳 `"git"` 或 `"cwd"`
  - `parse_created(value: str | None, fallback_mtime: float) -> datetime`：一律回傳 aware datetime；沒有時區的視為本機時區，`Z` 視為 UTC；解析失敗或缺值就用 mtime
  - CLI `list [--all] [--cwd DIR] [--now ISO]`，輸出 `{"scope", "items": [{"path", "task", "status", "created", "worktree", "branch", "current", "malformed"}], "remaining", "skipped": [{"path", "reason"}]}`

規則（D4、D5）：git 情境解析 `git worktree list --porcelain`，當前 worktree 是 `rev-parse --show-toplevel` 的 realpath；git 不可用或 cwd 不在 repo 內就是 `"cwd"` 情境。只看每個 `.claude/handoffs/` 頂層的 `*.md`。排除 `status == "resumed"`；`malformed` 和 `not_handoff` 都列出，標 `malformed: true`（`not_handoff` 的 `status` 是 `null`）。排序：`current` 優先，其次 `created` 新到舊。預設只保留 `now - 7 天` 以內、最多 5 份；`remaining` = 符合條件的總數減去顯示數。`--all` 時不限制，`remaining == 0`。`skipped` 的 reason：`"symlink"`（handoff 檔本身是 symlink）、`"missing_worktree"`、`"unreadable"`。

- [ ] **Step 1: 寫失敗的測試**

`class ListTests`，固定 `--now 2026-10-18T12:00:00+08:00`：
- `test_non_git_reads_cwd_only`：`scope == "cwd"`，列出一份，`current is True`，`branch is None`。
- `test_git_scans_all_worktrees_current_first`：主 checkout 一份、linked worktree 一份，從 linked worktree 執行 → `items[0]["current"] is True` 且來自 linked；兩份的 `branch` 都是對應的分支名稱。
- `test_subdirectory_cwd_uses_repo_root`：從 `repo/sub/` 執行，結果與從 repo 根目錄執行相同。
- `test_excludes_resumed`。
- `test_window_and_cap_with_remaining`：7 天內 7 份、8 天前 1 份 → `len(items) == 5`、`remaining == 3`。
- `test_all_lifts_window_and_cap`：同樣的資料加 `--all` → `len(items) == 8`、`remaining == 0`。
- `test_malformed_and_not_handoff_listed_with_flag`。
- `test_symlink_handoff_skipped`：`skipped == [{"path": …, "reason": "symlink"}]`。
- `test_missing_worktree_skipped`：`git worktree add` 後直接刪掉目錄、不 prune → reason `"missing_worktree"`。
- `test_created_missing_falls_back_to_mtime`：沒有 `created`，mtime 設成 10 天前 → 不在 items 中，`remaining == 0`。
- `test_created_formats_compare`：`2026-10-18T10:00:00`、`2026-10-18T03:00:00Z`、`2026-10-18T11:00:00+08:00` 三份 → exit 0，依時間排序。
- `test_unicode_and_space_filenames`：`feat-中文 x--20261018-100000.md` 照常列出。
- `test_git_unavailable_falls_back_to_cwd`：`PATH` 只包含 python 所在目錄 → `scope == "cwd"`、exit 0。

- [ ] **Step 2: 執行測試，確認失敗**

Run: `python3 -m unittest tests.test_session_start_handoffs.ListTests -v`
Expected: FAIL，原因是沒有 `list` 子指令。

- [ ] **Step 3: 在 `handoffs.py` 實作 `Location`、`discover_locations`、`parse_created` 和 `list` 子指令**

- [ ] **Step 4: 執行全部測試，確認通過**

Run: `python3 -m unittest tests.test_session_start_handoffs -v`
Expected: 全部 PASS。

- [ ] **Step 5: Commit（先問 Tom）**

```bash
git add session-start/scripts/handoffs.py tests/test_session_start_handoffs.py
git commit -m "feat(session-start): list unfinished handoffs across worktrees"
```

### Task 3: `mark-resumed`

**Files:**
- Modify: `session-start/scripts/handoffs.py`
- Modify: `tests/test_session_start_handoffs.py`

**Interfaces:**
- Consumes: `parse_handoff`（用 `body_offset` 確保內文 bytes 不變）。
- Produces: CLI `mark-resumed PATH --expect-sha256 HEX [--now ISO]`。成功時 exit 0，輸出 `{"path", "status": "resumed", "resumed_at"}`。拒絕時 exit 3，輸出 `{"error": E}`，`E` 是 `"hash_mismatch" | "already_resumed" | "malformed" | "not_handoff" | "symlink"`；檔案不存在時 exit 2，`{"error": "not_found"}`。

改寫規則：`status:` 那一行改成 `status: resumed`（行尾註解拿掉）。緊接在它後面放 `resumed_at: <now.isoformat(timespec="seconds")>`；已經有 `resumed_at` 行就取代，不另外新增。`body_offset` 之後的 bytes 原樣保留，原本的換行格式也保留。寫入方式：在同一個目錄建暫存檔，`chmod` 成原本的權限，再 `os.replace`。檢查順序：symlink → hash → kind → status。

- [ ] **Step 1: 寫失敗的測試**

`class MarkResumedTests`：
- `test_marks_status_and_adds_resumed_at`：`check` 後執行 → `fields["status"] == "resumed"`、`fields["resumed_at"] == "2026-10-18T12:00:00+08:00"`。
- `test_body_bytes_unchanged`：改寫前後，`body_offset` 之後的 bytes 相同。
- `test_hash_mismatch_refuses_and_leaves_file`：exit 3、`hash_mismatch`，檔案 bytes 不變。
- `test_already_resumed_refuses`、`test_malformed_refuses`、`test_symlink_refuses`。
- `test_permissions_preserved`：先 `chmod 0o600`，改寫後仍然是 `0o600`。
- `test_existing_resumed_at_replaced_not_duplicated`：原本有舊的 `resumed_at` → 改寫後只剩一行 `resumed_at:`。

- [ ] **Step 2: 執行測試，確認失敗**

Run: `python3 -m unittest tests.test_session_start_handoffs.MarkResumedTests -v`
Expected: FAIL，原因是沒有 `mark-resumed` 子指令。

- [ ] **Step 3: 在 `handoffs.py` 實作 `mark-resumed` 子指令**

- [ ] **Step 4: 執行全部測試，確認通過**

Run: `python3 -m unittest tests.test_session_start_handoffs -v`
Expected: 全部 PASS。

- [ ] **Step 5: Commit（先問 Tom）**

```bash
git add session-start/scripts/handoffs.py tests/test_session_start_handoffs.py
git commit -m "feat(session-start): mark a picked handoff resumed atomically"
```

### Task 4: `delegate`

**Files:**
- Modify: `session-start/scripts/handoffs.py`
- Modify: `tests/test_session_start_handoffs.py`

**Interfaces:**
- Consumes: `git`。
- Produces:
  - `SELF_SKILL: Path = Path(__file__).resolve().parent.parent / "SKILL.md"`
  - `user_level_roots(home: Path) -> list[Path]`：`home/.claude/skills`、`home/.codex/skills`、`home/.omp/agent/skills`、`home/.claude/plugins`、`home/.codex/plugins`
  - CLI `delegate --runtime {claude,codex} [--cwd DIR]`，輸出 `{"root", "delegate": str | null, "candidates": [str], "drift": bool, "excluded": [{"path", "reason"}]}`

規則（D1、D2）：`root` 是 git 根目錄，非 git 時是 cwd。候選順序：`claude` 先 `root/.claude/skills/session-start/SKILL.md`，再 `root/.codex/…`；`codex` 相反。只取存在的一般檔案（`is_file()`，會跟隨 symlink）。排除條件：
- realpath 等於 `SELF_SKILL.resolve()` → `"self"`。
- 字面路徑，或它的 realpath，位於任何一個 user-level root 底下（root 的字面形式和 resolve 後的形式都要比對）→ `"user_level"`。

剩下的候選用 realpath 去重，保留第一個。`delegate` 是第一個候選；`drift` 只有在去重後還剩兩份、而且兩份 bytes 不同時才是 `true`。`Path.home()` 取自 `HOME` 環境變數，測試用 `HOME` 指向暫存目錄。

- [ ] **Step 1: 寫失敗的測試**

`class DelegateTests`。腳本先複製到暫存目錄 `install/session-start/scripts/handoffs.py`，並放一份 `install/session-start/SKILL.md`，讓「self」跟候選檔分開：
- `test_no_candidate_returns_null`：`delegate is None`、`candidates == []`。
- `test_claude_runtime_prefers_dot_claude_and_reports_drift`：兩份內容不同的獨立檔案 → `delegate` 以 `/.claude/skills/session-start/SKILL.md` 結尾，`drift is True`。
- `test_codex_runtime_prefers_dot_codex`。
- `test_symlinked_codex_dir_dedupes`：`.codex/skills -> ../.claude/skills` → `len(candidates) == 1`、`drift is False`。
- `test_identical_distinct_files_no_drift`。
- `test_self_is_excluded`：執行的腳本就是 `root/.claude/skills/session-start/scripts/handoffs.py` → `delegate is None`，`excluded[0]["reason"] == "self"`。
- `test_user_level_excluded_in_non_git_home`：`HOME=tmp/home`，`home/.claude/skills` 是指向 `tmp/prod` 的 symlink，`prod/session-start/SKILL.md` 存在；以 `--cwd home` 執行 `install/` 的副本 → `delegate is None`，reason 是 `"user_level"`。
- `test_non_git_uses_cwd_root`：`root` 等於 cwd 的 realpath。

- [ ] **Step 2: 執行測試，確認失敗**

Run: `python3 -m unittest tests.test_session_start_handoffs.DelegateTests -v`
Expected: FAIL，原因是沒有 `delegate` 子指令。

- [ ] **Step 3: 在 `handoffs.py` 實作 `delegate` 子指令**

- [ ] **Step 4: 執行全部測試，確認通過**

Run: `python3 -m unittest tests.test_session_start_handoffs -v`
Expected: 全部 PASS。

- [ ] **Step 5: Commit（先問 Tom）**

```bash
git add session-start/scripts/handoffs.py tests/test_session_start_handoffs.py
git commit -m "feat(session-start): delegate to a repo-local session-start"
```

### Task 5: `SKILL.md` 與 Codex metadata

**Files:**
- Create: `session-start/SKILL.md`
- Create: `session-start/agents/openai.yaml`（內容與 `handoff/agents/openai.yaml` 相同：`policy.allow_implicit_invocation: false`）

**Interfaces:**
- Consumes: Task 1–4 的 CLI 與 JSON 欄位。腳本路徑寫成 `python3 <skill_base_directory>/scripts/handoffs.py`（沿用 `work-log-analyzer/SKILL.md` 的佔位寫法）。

SKILL.md 必須包含：
- frontmatter：`name: session-start`；description 以 `Use when` 開頭，寫出觸發詞 `/session-start`、`開工`、`接手交接`、`resume a handoff`，並說明只在使用者明確呼叫時執行。
- 流程：spec §4.2 的 8 個步驟，順序相同。步驟 2 寫明：`delegate` 不是 null 就讀那份 SKILL.md、照它執行、原樣傳入使用者參數，通用流程結束；`drift` 為 true 時提醒一句。`--runtime` 依目前所在的 runtime 填 `claude` 或 `codex`。
- 步驟 4 的表格欄位：編號、任務、status、建立時間、來源 worktree／分支；`malformed` 標「格式異常」；`remaining > 0` 時補「另有 N 份，加 `--all` 可列出」；`skipped` 不是空的就列出。
- 步驟 1（D7）：先取出 `--handoff <path>`、`--all`；以 `.md` 結尾且檔案存在的參數視為 handoff 路徑；其餘當任務描述。指定的路徑在 `check` 回傳 exit 2 時，說明它不是 handoff 並停止。
- 步驟 5：`worktree_matches_cwd` 為 false 時提醒一句。`already_resumed` 為 true 時先說明並詢問，確認後不呼叫 `mark-resumed`；不是的話，等使用者確認繼續後，帶 `check` 回傳的 `sha256` 呼叫 `mark-resumed`；exit 3 時照 `error` 說明，不重試。
- Error Handling：exit 2、exit 3 的意義與處理方式。
- Security：handoff 內容是不可信資料；只執行白名單 assertion；除了 `mark-resumed` 之外都是唯讀；不 fetch。
- Examples：無參數、帶任務描述、帶 handoff 路徑，各一個。

- [ ] **Step 1: 寫 `session-start/SKILL.md` 與 `session-start/agents/openai.yaml`**

- [ ] **Step 2: 執行 `skill-auditor`**

Run: 用 Skill tool 呼叫 `skill-auditor`，對象是 `session-start/`。
Expected: 沒有 high 或 medium 的發現；有的話修正後重跑。

- [ ] **Step 3: Commit（先問 Tom）**

```bash
git add session-start/SKILL.md session-start/agents/openai.yaml
git commit -m "feat(session-start): add skill workflow and Codex metadata"
```

### Task 6: catalog、router、CLAUDE.md 登記

**Files:**
- Modify: `skills-catalog.json`（新增 entry）
- Modify: `skill-router/skill-registry.yaml`（`dev-process` 區段，放在 `id: handoff` 之後）
- Modify: `CLAUDE.md`（Available Skills → Productivity & Analysis 新增一行）
- Modify（產生）: `SKILLS_CATALOG.md`

**Interfaces:**
- catalog entry：`{"id": "session-start", "category": "productivity-tracking", "lifecycle": "experimental", "invocation_intent": "user", "surfaces": {"routable": true, "listed_in_readme": false, "sync": true}}`
- router triggers：`"/session-start"`、`"開工"`、`"接手交接"`、`"resume handoff"`、`"session start"`。不要使用 `handoff` 已經用掉的觸發詞（`收工`、`交接`）。
- CLAUDE.md：`- **session-start** — Resume unfinished handoffs across worktrees, delegating to a repo-local session-start when one exists`

- [ ] **Step 1: 修改上面三個檔案**

- [ ] **Step 2: 重新產生並檢查**

Run: `python3 scripts/validate_skills_catalog.py --write && python3 scripts/validate_skills_catalog.py --check`
Expected: exit 0；`SKILLS_CATALOG.md` 多一列 session-start。

- [ ] **Step 3: Commit（先問 Tom）**

```bash
git add skills-catalog.json skill-router/skill-registry.yaml CLAUDE.md SKILLS_CATALOG.md
git commit -m "chore(catalog): register session-start"
```

### Task 7: 打包進 repo-workflow

**Files:**
- Modify: `plugin-packages.json`：`repo-workflow.skills` 加入 `"session-start"`；`runtime_resources` 加入 `"session-start/scripts/handoffs.py"`、`"session-start/agents/openai.yaml"`；`version` 不動。
- Modify: `scripts/plugin_packaging/catalog.py:92-93`：`38` → `39`（兩處數字和錯誤訊息）。
- Modify: `tests/test_plugin_packages.py`：`APPROVED['repo-workflow']` 改成 `'code-story-teller repo-sync handoff session-start'`；`:33` 改成 `(39, 39)`。
- Modify: 待重驗的文字（保留被釘住的片語 `need native acceptance again before release`、`發布前需要重新驗收`）：
  - `README.md:21`：`38 source skills` → `39 source skills`；`session-preferences and work-journal changed afterward` → `session-preferences, work-journal, repo-workflow and skill-toolbox changed afterward`
  - `README.zh.md:21`：`38 個來源 skills` → `39 個來源 skills`；`` `session-preferences` 與 `work-journal` 在那之後有修改`` → `` `session-preferences`、`work-journal`、`repo-workflow` 與 `skill-toolbox` 在那之後有修改``
  - `docs/plugins/README.md:3`：同 README.zh.md 的修改方式；`:9` repo-workflow 那一列加上「開工時接手交接」；`:15` `38` → `39`
  - `docs/plugins/installation.md:3`：同 README.zh.md 的修改方式
  - `scripts/plugin_packaging/render.py:154-155`：`session-preferences and work-journal changed after that run` → `session-preferences, work-journal, repo-workflow and skill-toolbox changed after that run`
  - `docs/validation/skill-plugins/acceptance.json` 的 `limits`：新增一條 `"repo-workflow (session-start added) and skill-toolbox (package index) changed after the recorded run; their recorded bindings are stale."`
- Modify: `tests/test_build_plugins.py`：新增 `test_docs_name_repo_workflow_for_reacceptance`
- Modify（產生）: `plugins/claude/**`、`plugins/codex/**`

- [ ] **Step 1: 寫失敗的測試**

- `tests/test_plugin_packages.py` 的 membership 測試（因 APPROVED 與 39 而失敗）。
- `test_docs_name_repo_workflow_for_reacceptance`：
  - `README.md` 含有 `repo-workflow and skill-toolbox changed afterward`。
  - `README.zh.md`、`docs/plugins/README.md`、`docs/plugins/installation.md` 都含有 `` `repo-workflow` 與 `skill-toolbox` 在那之後有修改``。
  - 每個 `plugins/*/*/README.md` 都含有 `repo-workflow and skill-toolbox changed after that run`。

- [ ] **Step 2: 執行測試，確認失敗**

Run: `python3 -m unittest tests.test_plugin_packages tests.test_build_plugins -v`
Expected: 上面兩個測試 FAIL。

- [ ] **Step 3: 修改 Files 列出的來源檔，然後重建**

Run: `python3 scripts/build_plugins.py --write`
Expected: exit 0；`plugins/claude/repo-workflow/skills/session-start/` 和 `plugins/codex/repo-workflow/skills/session-start/` 都出現 `SKILL.md`、`scripts/handoffs.py`、`agents/openai.yaml`；兩個平台的 `skill-toolbox/skills/package-index.json` 都有 `repo-workflow:session-start`。

- [ ] **Step 4: 執行完整檢查**

Run: `python3 scripts/build_plugins.py --check && python3 scripts/check_plugin_release.py && python3 scripts/validate_skills_catalog.py --check && python3 -m unittest discover -s tests`
Expected: 全部 exit 0；unittest 顯示 `OK`。

- [ ] **Step 5: Commit（先問 Tom）**

```bash
git add plugin-packages.json scripts/plugin_packaging/catalog.py scripts/plugin_packaging/render.py tests/test_plugin_packages.py tests/test_build_plugins.py README.md README.zh.md docs/plugins/README.md docs/plugins/installation.md docs/validation/skill-plugins/acceptance.json plugins/
git commit -m "feat(plugins): package session-start in repo-workflow"
```

### Task 8: 最終驗證與唯讀實測

**Files:** 無變更。

- [ ] **Step 1: 完整檢查**

Run: `python3 scripts/build_plugins.py --check && python3 scripts/check_plugin_release.py && python3 scripts/validate_skills_catalog.py --check && python3 -m unittest discover -s tests && (cd skills-query-server && npm test)`
Expected: 全部 exit 0。

- [ ] **Step 2: 用真實的 repo 做唯讀實測**

在兩個有 repo-local `session-start` 的本機 repo（路徑記在交接檔，不寫進公開文件），各執行：
- `python3 session-start/scripts/handoffs.py delegate --runtime claude --cwd <repo>` → `delegate` 的 realpath 等於 `<repo>/.claude/skills/session-start/SKILL.md`。
- 同一個指令改用 `--runtime codex` → `delegate` 的 realpath 相同，`drift` 是 `false`。

在本 worktree 執行 `python3 session-start/scripts/handoffs.py list` → items 裡有主 checkout 的 `main--20261018-203410.md`，`current` 是 `false`、`branch` 是 `main`。

- [ ] **Step 3: 用 `completion-gate` 確認完成**，並把 Step 1、Step 2 的實際輸出摘要回報給 Tom。

合進 `production` 之後的實測（spec §8 第 2 步）不屬於這個 PR，列為後續步驟。
