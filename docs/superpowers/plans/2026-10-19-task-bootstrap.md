# task-bootstrap (PR-2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增 user-level `task-bootstrap` skill：先跑 `session-start`，再替新任務建立分支與 git worktree；登記進 catalog 並打包進 `repo-workflow`。

**Architecture:** `task-bootstrap/scripts/bootstrap_worktree.py` 是單檔標準函式庫 CLI，有 `delegate` 與 `create` 兩個子指令，輸出都是 JSON。`create` 不加 `--execute` 只算計畫、不改任何東西，加了才執行。`task-bootstrap/SKILL.md` 負責編排與對話。測試放頂層 `tests/`，用 subprocess 跑 CLI，搭配暫存 git repo 與本機 bare remote（`file://`）。

**Tech Stack:** Python 3.12 標準函式庫、git CLI、`unittest`。

**Spec:** `docs/superpowers/specs/2026-10-18-session-start-task-bootstrap-design.md`（本計畫涵蓋 D3、D9–D17 與 §4.3、§5、§6、§7；`session-start` 已在 PR-1 完成）。

## Global Constraints

- 只用 Python 標準函式庫與 git CLI；subprocess 一律傳參數陣列，不用 `shell=True`。
- 呼叫 git 前先從環境變數清掉會選定 repo 的那些（`GIT_DIR`、`GIT_WORK_TREE`、`GIT_INDEX_FILE`、`GIT_OBJECT_DIRECTORY`、`GIT_ALTERNATE_OBJECT_DIRECTORIES`、`GIT_COMMON_DIR`、`GIT_PREFIX`、`GIT_NAMESPACE`、`GIT_CEILING_DIRECTORIES`），保留 `GIT_CONFIG_GLOBAL`、`GIT_CONFIG_NOSYSTEM`，並設 `GIT_OPTIONAL_LOCKS=0`、`GIT_TERMINAL_PROMPT=0`。PR-1 的審查發現，不清的話在 hook 裡執行會對錯的 repo 回報結果。
- 腳本不 stage、commit、push、rebase、merge、stash、reset、clean，也不刪任何東西；唯一的寫入型 git 指令是 `fetch`、`pull --ff-only`（只在 `main` 模式）與 `worktree add`。不印檔案內容。
- clean-room（D15）：不讀、不複製任何既有 repo-local 實作；提交的檔案（含 commit 訊息與本計畫）不寫那些 repo 的名稱或內部細節。
- `repo-workflow` 版號維持 `0.1.0`（D16）。
- 程式碼註解用英文，只解釋「為什麼」。
- 測試從 repo 根目錄跑：`python3 -m unittest tests.test_task_bootstrap -v`。測試只在暫存目錄建 repo，子行程的 `HOME` 指向暫存目錄、`GIT_CONFIG_GLOBAL=os.devnull`，不碰真實的 `~` 與任何真實 repo。worktree 需先在 `skills-query-server/` 跑過 `npm ci`（本分支已做）。
- 每個 Commit 步驟都要先取得 Tom 同意（PR-1 的授權只限舊分支）；commit 前依 `completion-gate` 判斷 L0／L1／L2，L1／L2 用 `code-review-claude`；訊息遵守 Conventional Commits，結尾加 `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`。
- 每個 commit 都要讓 `python3 scripts/build_plugins.py --check` 通過：改 catalog 或 `plugin-packages.json` 的 commit，要同時提交 `build_plugins.py --write` 的產出（PR-1 的 `ced265a` 因此失敗過）。
- 第一個 commit 只放本計畫：`docs(plans): add task-bootstrap implementation plan`。

## 計畫補充的決定（spec 沒寫，執行者照這裡做）

- 子指令叫 `create`。`--task` 只原樣放進輸出的 `task`，不寫檔、不影響行為。
- 「來源乾淨」指 `git status --porcelain --untracked-files=no` 為空。未追蹤檔不算，因為 `.env` 本來就是未追蹤的。
- 新分支一律 `--no-track`；只有 `baseline` 用 `--track`。理由：upstream 指向 `origin/main` 的功能分支，在 `push.default=upstream` 下一個 `git push` 就會推到 main。
- `baseline` 先 `fetch <remote> <branch>`，否則 `<remote>/<branch>` 可能不存在（spec 表格沒列這步）。
- slug 由分支名取得：`/` 換成 `-` 再轉小寫。`--slug` 直接給的不轉換。兩者都要符合 `^[a-z0-9][a-z0-9._-]*$`，不符合就 `slug_invalid`，不偷偷清洗。
- `task` 模式的「目前就在 `--base-ref` 上」：source 的 `HEAD` commit 等於 `<base-ref>^{commit}`。
- 預設分支的 fallback 用 `git ls-remote --heads <remote> main master`（唯讀、不 fetch），所以 dry-run 也能用。
- remote URL 白名單：`https://`、`ssh://`、`git://`、`file://`，以及 scp 格式 `[user@]host:path`（user 可省略，因為 ssh config 別名常這樣寫；`path` 不能以 `:` 或 `//` 開頭、不能含空白，`host` 第一個字元要是英數）。`http://`、本機路徑、`ext::`、`fd::`、`-` 開頭一律拒絕。
- `git check-ref-format --branch` 會展開 `@{-1}`，所以 `validate_branch` 要求它的輸出等於輸入，且輸入不以 `-` 開頭。
- 明確指定卻做不到的（`--copy`、`--copy-venv`）→ `copy_rejected`；只有隱含的 `.env` 與 `.codex/skills` symlink 缺席時才是跳過。
- 「要複製的檔案在目標已存在」只在 `--execute` 建好 worktree 之後檢查，dry-run 不預測。
- 退出碼：0 成功；2 參數錯誤或路徑不存在；3 拒絕（stop condition），stdout 是 `{"error": CODE, ...}`。

## Review Focus

1. 來源有未追蹤的 `.env`（正是要複製的那個檔）：不能被當成「不乾淨」。→ Task 2 `test_untracked_files_do_not_make_source_dirty`。
2. remote 用 ssh config 別名（`alias:owner/repo.git`，沒有 `user@`）：要放行；`ext::…` 要擋。→ Task 2 `test_remote_url_allowlist`。
3. 從 linked worktree 裡執行：`main` 模式的來源與目標根目錄仍以主 checkout 為準，不是 cwd。→ Task 2 `test_default_source_is_main_checkout_from_linked_worktree`。
4. 分支名帶斜線或大寫（`Fix/Login`）：slug 變成 `fix-login`；無法轉成合法 slug 的（例如含 `é`）要求使用者給 `--slug`。→ Task 2 `test_slug_rules`。
5. remote 沒有 `refs/remotes/<remote>/HEAD`（用 `git remote add` 加的 remote 常見）：靠 `ls-remote` 補，不要求使用者先 `set-head`。→ Task 2 `test_default_branch_from_ls_remote_when_head_missing`。

---

### Task 1: 腳本骨架與 `delegate`

**Files:**
- Create: `task-bootstrap/scripts/bootstrap_worktree.py`
- Create: `tests/test_task_bootstrap.py`

**Interfaces:**
- Produces（`bootstrap_worktree.py`）：
  - `GIT_TIMEOUT_SECONDS = 10`、`NETWORK_TIMEOUT_SECONDS = 60`
  - `git(args: list[str], cwd: Path, *, timeout: int = GIT_TIMEOUT_SECONDS) -> subprocess.CompletedProcess[str] | None`：git 不存在或逾時回傳 `None`；依 Global Constraints 清理環境變數。
  - `SELF_SKILL: Path = Path(__file__).resolve().parent.parent / "SKILL.md"`
  - `user_level_roots(home: Path) -> list[Path]`：`home/.claude/skills`、`home/.codex/skills`、`home/.omp/agent/skills`、`home/.claude/plugins`、`home/.codex/plugins`（與 `session-start/scripts/handoffs.py` 的同名函式結果相同，但不 import 它，D14）
  - `emit(payload: dict, code: int = 0) -> int`：JSON 用 `ensure_ascii=False` 印到 stdout，回傳 `code`
  - `main(argv: list[str] | None = None) -> int`，CLI `delegate --runtime {claude,codex} [--cwd DIR]`
- Produces（測試檔，後續 Task 共用）：`SCRIPT`、`GIT_ENV`（`GIT_CONFIG_GLOBAL=os.devnull`、`GIT_CONFIG_NOSYSTEM=1`、固定 author／committer）、`@dataclass Project: tmp, origin, main`、`make_project(tmp: Path) -> Project`（`tmp/origin.git` 是 `git init --bare -b main`；`tmp/proj` 由 `file://` clone 而來，有一個初始 commit 已 push，`origin/HEAD` 已設定）、`run_script(*args: str, cwd: Path, env: dict | None = None) -> tuple[int, dict]`（子行程 `HOME=tmp/home`、移除繼承的 `GIT_*`）、`run_create(project: Project, *args: str, cwd: Path | None = None) -> tuple[int, dict]`（呼叫 `create`，預設 cwd 是 `project.main`）、`git_out(cwd: Path, *args: str) -> str`。

`delegate` 規則（D3，與 `session-start` 的 `delegate` 同一套，只差名稱）：`root` 是 `rev-parse --show-toplevel`，非 git 時是 cwd 的 realpath。依 runtime 順序掃 `root/.claude/skills/*/SKILL.md` 與 `root/.codex/skills/*/SKILL.md`（`claude` 先 `.claude`，`codex` 先 `.codex`），目錄名稱以 `task-bootstrap` 結尾的才算（含 `task-bootstrap` 本身），只取 `is_file()` 的檔案。排除：realpath 等於 `SELF_SKILL.resolve()` → `self`；字面路徑或 realpath 位於 `user_level_roots(Path.home())` 底下 → `user_level`；讀不到 → `unreadable`（改用同名的下一個候選）。同一個目錄名稱下，剩下的候選用 realpath 去重、保留第一個；`drift` 只在去重後還剩兩份且 bytes 不同時為 `true`。輸出 `{"root", "candidates": [{"name", "path", "drift"}], "excluded": [{"path", "reason"}]}`，`candidates` 依 `name` 排序。`--cwd` 不存在時 exit 2、`{"error": "not_found"}`。

- [ ] **Step 1: 寫失敗的測試**

`class DelegateTests`，腳本先複製到暫存目錄 `install/task-bootstrap/scripts/bootstrap_worktree.py` 並放一份 `install/task-bootstrap/SKILL.md`，讓「self」與候選檔分開：
- `test_no_candidate_returns_empty`：`candidates == []`。
- `test_prefixed_variant_found`：`.claude/skills/acme-task-bootstrap/SKILL.md` → `candidates == [{"name": "acme-task-bootstrap", "path": …, "drift": False}]`。
- `test_several_variants_sorted_by_name`：兩個前綴不同的目錄 → 依名稱排序。
- `test_runtime_order_and_drift`：同名、兩份內容不同 → `claude` 的 `path` 含 `/.claude/skills/`、`codex` 的含 `/.codex/skills/`，`drift is True`。
- `test_symlinked_codex_dir_dedupes`：`.codex/skills -> ../.claude/skills` → 一個 candidate、`drift is False`。
- `test_self_is_excluded`：執行的腳本位於 `root/.claude/skills/task-bootstrap/scripts/` → `candidates == []`、`excluded[0]["reason"] == "self"`。
- `test_user_level_excluded`：`HOME=tmp/home`，`home/.claude/skills` 是指向 `tmp/prod` 的 symlink，`prod/acme-task-bootstrap/SKILL.md` 存在，`--cwd home` → `candidates == []`、reason 是 `"user_level"`。
- `test_unreadable_candidate_falls_to_next`：`.claude` 那份 `chmod 0`，`.codex` 那份可讀 → `path` 是 `.codex` 那份，`excluded` 有 `"unreadable"`（`os.geteuid() == 0` 時 `skipTest`）。
- `test_non_git_uses_cwd_root`、`test_missing_cwd_exits_2`：`(2, {"error": "not_found"})`。

`class HelperTests`：
- `test_fixture_isolated_from_global_git_config`：在 fixture repo 裡 `git config --get core.excludesFile`（帶 `GIT_ENV`）的回傳碼不是 0，確保測試結果不會因使用者的全域 git 設定而不同。
- `test_user_level_roots_match_session_start`：用 `importlib.util.spec_from_file_location` 載入兩支腳本，同一個 `home` 下 `user_level_roots` 回傳相同的清單。
- `test_inherited_git_dir_is_ignored`：`os.environ["GIT_DIR"]` 指向另一個 repo 時，`git(["rev-parse", "--show-toplevel"], cwd=project.main)` 仍回報 `project.main`。

- [ ] **Step 2: 執行測試，確認失敗**

Run: `python3 -m unittest tests.test_task_bootstrap -v`
Expected: FAIL／ERROR，原因是 `task-bootstrap/scripts/bootstrap_worktree.py` 不存在。

- [ ] **Step 3: 實作上面 Interfaces 列出的內容**

`delegate` 的候選收集與 `session-start` 同形，但按目錄名稱分組；不 import `handoffs.py`。

- [ ] **Step 4: 執行測試，確認通過**

Run: `python3 -m unittest tests.test_task_bootstrap -v`
Expected: 全部 PASS。

- [ ] **Step 5: Commit（先問 Tom）**

```bash
git add task-bootstrap/scripts/bootstrap_worktree.py tests/test_task_bootstrap.py
git commit -m "feat(task-bootstrap): delegate to a repo-local task-bootstrap"
```

### Task 2: `create` 的共用檢查與 `main` 模式計畫

**Files:**
- Modify: `task-bootstrap/scripts/bootstrap_worktree.py`
- Modify: `tests/test_task_bootstrap.py`

**Interfaces:**
- Consumes: Task 1 的 `git`、`emit`、測試 fixture。
- Produces:
  - `class Refusal(Exception)`：屬性 `code: str`、`detail: dict`；`main` 捕捉後 `emit({"error": code, **detail}, 3)`。
  - `validate_branch(name: str) -> str`、`derive_slug(branch: str) -> str`、`validate_slug(slug: str) -> str`、`remote_url_allowed(url: str) -> bool`（規則見「計畫補充的決定」）
  - `find_main_checkout(anchor: Path) -> Path`：anchor 所屬 repo 的 `git worktree list --porcelain` 第一筆；不在 git 內 → `Refusal("source_not_git")`
  - `detect_default_branch(source: Path, remote: str, override: str | None) -> str`：`override` 優先（仍要通過 `validate_branch`）；其次 `symbolic-ref --short refs/remotes/<remote>/HEAD` 去掉 `<remote>/`；再其次 `ls-remote --heads <remote> main master` 恰好一個；否則 `Refusal("default_branch_unknown")`
  - `resolve_target(worktrees_root: Path, repo_name: str, slug: str) -> Path`：`worktrees_root` 與 `worktrees_root/repo_name` 若存在且是 symlink → `Refusal("parent_symlink")`；結果 resolve 後必須在 `worktrees_root` resolve 後的路徑底下，否則 `Refusal("target_outside_root")`；`os.path.lexists(target)` → `Refusal("target_exists")`
  - `build_plan(args: argparse.Namespace) -> dict`、`cmd_create(args) -> int`
  - CLI `create`，參數：`--mode {main,baseline,task}`（預設 `main`）、`--branch`（必填）、`--slug`、`--task`、`--source`、`--base-ref`、`--remote`（預設 `origin`）、`--default-branch`、`--worktrees-root`、`--asset-source`、`--copy-venv`、`--copy PATH`（可重複）、`--execute`、`--cwd`。非 `main` 模式在 Task 3 之前回 `Refusal("mode_unsupported")`。
- 計畫 JSON（本 Task 起固定，後續 Task 只填內容）：`{"mode", "task", "source", "asset_source", "remote", "default_branch", "base_ref", "branch", "slug", "target", "worktrees_root", "commands", "copies", "skipped_copies", "symlink", "executed"}`。路徑都是 realpath 字串；`commands` 是參數陣列的清單，每筆以 `["git", "-C", <source>]` 開頭；`copies`、`skipped_copies` 先是 `[]`、`symlink` 先是 `null`（Task 4 填）；`executed` 是 `false`。

定位與預設：`anchor = --source 或 --cwd`；`main_checkout = find_main_checkout(anchor)`；`source`、`asset_source` 預設是 `main_checkout`；`repo_name = main_checkout.name`；`worktrees_root` 優先序 `--worktrees-root` > 環境變數 `TASK_BOOTSTRAP_WORKTREES_ROOT` > `main_checkout.parent / "worktrees"`；`target = worktrees_root / repo_name / slug`（D12）。

`main` 模式檢查順序（全部通過才輸出計畫）：remote 名稱在 `git remote` 內（`remote_invalid`）→ `git remote get-url <remote>` 通過白名單（`remote_url_rejected`）→ 預設分支 → 來源乾淨（`source_dirty`）→ 來源目前分支等於預設分支，detached 也算不符（`source_branch_mismatch`）→ `validate_branch`（`branch_invalid`）、slug（`slug_invalid`）→ `refs/heads/<branch>` 不存在（`branch_exists`）→ `resolve_target`。`commands`：`fetch <remote>`；`pull --ff-only <remote> <default>`；`worktree add --no-track -b <branch> <target> <remote>/<default>`。`base_ref` 是 `<remote>/<default>`。

- [ ] **Step 1: 寫失敗的測試**

`class CreateMainPlanTests`，用 `run_create(project, "--branch", "feat/x")`：
- `test_main_plan_shape`：exit 0；`mode == "main"`、`default_branch == "main"`、`base_ref == "origin/main"`、`slug == "feat-x"`、`target` 的 realpath 等於 `tmp/worktrees/proj/feat-x` 的 realpath、`executed is False`；`commands` 的三筆正好是上面三個指令（含 `-C` 與絕對路徑）。
- `test_dry_run_changes_nothing`：前後比較 `git for-each-ref`、`git worktree list`、source 的 `rev-parse HEAD`、`tmp` 底下的路徑集合（不應出現 `worktrees/`）。
- `test_default_source_is_main_checkout_from_linked_worktree`：先建 linked worktree，從裡面執行 → `source` 與 `target` 仍以主 checkout 為準。
- `test_untracked_files_do_not_make_source_dirty`：source 有未追蹤的 `.env` → exit 0。`test_modified_tracked_file_refuses_source_dirty`：改動已追蹤檔 → `(3, error == "source_dirty")`。
- `test_source_on_other_branch_refuses`、`test_detached_head_refuses`：`source_branch_mismatch`。
- `test_default_branch_from_origin_head`；`test_default_branch_from_ls_remote_when_head_missing`（`git remote set-head origin -d` 後仍是 `main`）；`test_default_branch_unknown_when_main_and_master_both_exist`（`default_branch_unknown`）；`test_default_branch_override`（remote 只有 `trunk`，`--default-branch trunk` 成功，沒給則 `default_branch_unknown`）。
- `test_remote_url_allowlist`（直接呼叫 `remote_url_allowed`）：放行 `https://h/o/r.git`、`ssh://git@h/o/r.git`、`git://h/r.git`、`file:///tmp/r.git`、`git@h:o/r.git`、`alias:o/r.git`；拒絕 `http://h/r.git`、`ext::sh -c id`、`fd::3`、`/tmp/r.git`、`-oProxyCommand=x`、空字串。
- `test_remote_name_must_exist`（`--remote nope` → `remote_invalid`）；`test_rejected_remote_url_refuses_before_any_network`（`git remote set-url origin 'ext::sh -c true'` → `remote_url_rejected`）。
- `test_branch_validation`：`bad..name`、`-x`、`a b`、`x.lock`、`@{-1}` 都是 `branch_invalid`。
- `test_slug_rules`：`--branch Fix/Login` → `slug == "fix-login"`；`--slug ../x`、`--slug .`、`--slug Upper` → `slug_invalid`；`--branch feat/é` → `slug_invalid`，加 `--slug feat-e` 後成功。
- `test_branch_exists_refuses`、`test_target_exists_refuses`、`test_symlinked_worktrees_root_refuses`、`test_symlinked_repo_dir_refuses`（`worktrees/proj` 是 symlink）。
- `test_worktrees_root_precedence`：環境變數改變 `target`，`--worktrees-root` 再蓋過環境變數。
- `test_task_text_echoed_verbatim`：`--task 'fix login'` → `task == "fix login"`。

- [ ] **Step 2: 執行測試，確認失敗**

Run: `python3 -m unittest tests.test_task_bootstrap.CreateMainPlanTests -v`
Expected: FAIL，原因是沒有 `create` 子指令。

- [ ] **Step 3: 實作 Interfaces 列出的函式與 `create`（`main` 模式、不含 `--execute`）**

`ls-remote` 與其他唯讀網路呼叫用 `NETWORK_TIMEOUT_SECONDS`。

- [ ] **Step 4: 執行全部測試，確認通過**

Run: `python3 -m unittest tests.test_task_bootstrap -v`
Expected: 全部 PASS。

- [ ] **Step 5: Commit（先問 Tom）**

```bash
git add task-bootstrap/scripts/bootstrap_worktree.py tests/test_task_bootstrap.py
git commit -m "feat(task-bootstrap): plan a main-mode worktree without side effects"
```

### Task 3: `baseline` 與 `task` 模式計畫

**Files:**
- Modify: `task-bootstrap/scripts/bootstrap_worktree.py`
- Modify: `tests/test_task_bootstrap.py`

**Interfaces:**
- Consumes: Task 2 的 `build_plan`、`Refusal`、檢查函式。
- Produces: `build_plan` 支援三種模式；計畫 JSON 欄位不變。

`baseline`：remote 名稱與 URL 檢查同 `main`；`git ls-remote --heads <remote> <branch>` 要有輸出，否則 `branch_missing_on_remote`；`refs/heads/<branch>` 已存在 → `branch_exists`；不要求來源乾淨；`default_branch` 是 `null`、`base_ref` 是 `<remote>/<branch>`；`commands`：`fetch <remote> <branch>`；`worktree add --track -b <branch> <target> <remote>/<branch>`。

`task`：不檢查 remote，`default_branch` 是 `null`。必須有 `--base-ref`（`base_ref_required`）；`rev-parse --verify <base-ref>^{commit}` 要成功（`base_ref_invalid`）；source 乾淨（`source_dirty`）；source 的 `HEAD` commit 等於 base-ref 的 commit（`base_ref_mismatch`）；source 與 asset_source 的 `rev-parse --git-common-dir` realpath 相同（`source_wrong_repo`）。`commands` 只有 `worktree add --no-track -b <branch> <target> <base-ref>`。

- [ ] **Step 1: 寫失敗的測試**

`class CreateOtherModesTests`（remote 事先 push 一個 `release/1.0` 分支）：
- `test_baseline_plan`：`commands` 正好是上面兩筆；`copies == []`、`skipped_copies == []`、`default_branch is None`、`base_ref == "origin/release/1.0"`。
- `test_baseline_branch_missing_on_remote_refuses`、`test_baseline_local_branch_exists_refuses`、`test_baseline_ignores_dirty_source`。
- `test_task_plan`：`--source` 是停在 `feat/a` 的 linked worktree，`--base-ref feat/a`，新分支 `feat/b` → `commands` 只有一筆 `worktree add --no-track -b feat/b <target> feat/a`，沒有 `fetch`。
- `test_task_requires_base_ref`、`test_task_base_ref_must_resolve`、`test_task_source_must_be_on_base_ref`、`test_task_dirty_source_refuses`。
- `test_task_source_wrong_repo_refuses`：`--source` 是另一個無關的 repo → `source_wrong_repo`。
- `test_task_mode_works_without_remote`：沒有任何 remote 的 repo 照常出計畫。

- [ ] **Step 2: 執行測試，確認失敗**

Run: `python3 -m unittest tests.test_task_bootstrap.CreateOtherModesTests -v`
Expected: FAIL，原因是這兩種模式回 `mode_unsupported`。

- [ ] **Step 3: 實作兩種模式，移除 `mode_unsupported`**

- [ ] **Step 4: 執行全部測試，確認通過**

Run: `python3 -m unittest tests.test_task_bootstrap -v`
Expected: 全部 PASS。

- [ ] **Step 5: Commit（先問 Tom）**

```bash
git add task-bootstrap/scripts/bootstrap_worktree.py tests/test_task_bootstrap.py
git commit -m "feat(task-bootstrap): plan baseline and task modes"
```

### Task 4: 本機檔案與 symlink 計畫

**Files:**
- Modify: `task-bootstrap/scripts/bootstrap_worktree.py`
- Modify: `tests/test_task_bootstrap.py`

**Interfaces:**
- Consumes: Task 2–3 的 `build_plan`。
- Produces: `plan_local_files(asset_source: Path, copy_venv: bool, extra: list[str]) -> tuple[list[dict], list[dict], dict]`，回傳 `(copies, skipped_copies, symlink)`；`main`、`task` 模式的計畫用它填欄位，`baseline` 固定 `copies == []`、`symlink == {"action": "skip", "path": ".codex/skills", "link": "../.claude/skills", "reason": "baseline_mode"}`。
  - `copies` 每筆 `{"path": str, "type": "file" | "dir", "bytes": int}`（`dir` 的 `bytes` 是底下一般檔案大小總和，不跟隨 symlink）；`path` 是相對於 asset_source 的 POSIX 路徑。
  - `skipped_copies` 每筆 `{"path": str, "reason": str}`；`reason` 是 `absent`、`tracked`、`not_regular` 其中之一，只用於隱含的 `.env`。
  - `symlink`：`{"action": "create" | "skip", "path": ".codex/skills", "link": "../.claude/skills", "reason": str | None}`；`skip` 的 `reason` 是 `absent`、`not_symlink`、`different_target`、`tracked`。

規則（D13）：`.env` 一律檢查；`.venv` 只在 `copy_venv` 時；`extra` 每筆是 `--copy` 的值。`--copy` 與 `.venv` 的限制：相對路徑、不含 `..` 或 NUL 或換行、resolve 後在 asset_source 的 realpath 底下、`.venv` 之外只收一般檔案（`lstat` 為一般檔案，symlink 與目錄都不收）、必須是 git 未追蹤（`ls-files -- <path>` 沒有輸出）；任一不符 → `Refusal("copy_rejected", {"path": …, "reason": …})`。重複的路徑（正規化後相同）只算一筆。symlink：asset_source 的 `.codex/skills` 是 symlink、`readlink` 等於 `../.claude/skills`、且未被追蹤，才是 `create`。

- [ ] **Step 1: 寫失敗的測試**

`class LocalFilesTests`：
- `test_env_planned_when_untracked_regular_file`：`copies == [{"path": ".env", "type": "file", "bytes": <size>}]`。
- `test_env_absent_tracked_and_symlink_are_skipped`：三種情況的 reason 依序是 `absent`、`tracked`、`not_regular`，exit 都是 0。
- `test_venv_needs_flag`：沒給 `--copy-venv` → `copies` 沒有 `.venv`；給了 → `{"path": ".venv", "type": "dir", "bytes": …}`。`test_copy_venv_absent_refuses`：`copy_rejected`。
- `test_copy_boundaries`：下列都是 `copy_rejected`：絕對路徑、`../x`、目錄、symlink、已追蹤的檔案、不存在的檔案、經由指向外部的 symlink 目錄（`link/secret`）、含換行的路徑；`config/local.json`（未追蹤的巢狀檔案）則被接受。
- `test_copy_repeatable_and_deduped`：`--copy a --copy ./a --copy b` → `copies` 兩筆。
- `test_symlink_plan_cases`：來源有未追蹤的 `.codex/skills -> ../.claude/skills` → `create`；已追蹤 → `tracked`；不存在 → `absent`；指向別處 → `different_target`；一般目錄 → `not_symlink`。
- `test_baseline_has_no_local_files`：`baseline` 模式即使有未追蹤的 `.env` 與符合條件的 symlink，`copies == []`，`symlink["reason"] == "baseline_mode"`。
- `test_asset_source_defaults_to_main_checkout_and_can_be_overridden`。
- `test_plan_never_contains_file_contents`：`.env` 寫入一段獨特字串，stdout 不含它。

- [ ] **Step 2: 執行測試，確認失敗**

Run: `python3 -m unittest tests.test_task_bootstrap.LocalFilesTests -v`
Expected: FAIL，原因是 `copies`、`symlink` 還是空值。

- [ ] **Step 3: 實作 `plan_local_files` 並接進 `build_plan`**

- [ ] **Step 4: 執行全部測試，確認通過**

Run: `python3 -m unittest tests.test_task_bootstrap -v`
Expected: 全部 PASS。

- [ ] **Step 5: Commit（先問 Tom）**

```bash
git add task-bootstrap/scripts/bootstrap_worktree.py tests/test_task_bootstrap.py
git commit -m "feat(task-bootstrap): plan local file copies and the skills symlink"
```

### Task 5: `--execute`

**Files:**
- Modify: `task-bootstrap/scripts/bootstrap_worktree.py`
- Modify: `tests/test_task_bootstrap.py`

**Interfaces:**
- Consumes: Task 2–4 的計畫 JSON。
- Produces: `execute_plan(plan: dict) -> dict`，回傳計畫加上 `executed: true` 與 `head`（新 worktree 的 `rev-parse HEAD`）；`cmd_create` 在 `--execute` 時呼叫它。新增 `Refusal` 代碼：`fetch_failed`、`pull_failed`、`worktree_add_failed`（都附 `detail`：stderr 前 500 字，或 `"timeout"`）、`target_has_staged`、`copy_target_exists`。

執行順序：`commands` 逐筆執行（`fetch` 與 `pull` 用 `NETWORK_TIMEOUT_SECONDS`），任一失敗立刻停止，不重試。`worktree add` 成功之後：新 worktree 有 staged 檔案 → `target_has_staged`；再複製 `copies`（保留權限；目錄用 `shutil.copytree(symlinks=True)`；目標路徑已存在 → `copy_target_exists`）；最後建 `symlink`（先 `mkdir -p` 目標的 `.codex`；目標已存在就略過並不報錯）。`worktree add` 之後的任何失敗，輸出都要加 `"partial": {"target": …, "branch": …}`，worktree 與分支原樣保留，不清理。所有拒絕與驗證都在第一個寫入型指令之前完成。

- [ ] **Step 1: 寫失敗的測試**

`class ExecuteTests`。`git` 呼叫的紀錄用 PATH 前面的 shim：每次呼叫把 argv 寫進紀錄檔，再 `exec` 真正的 git。
- `test_main_execute_creates_worktree_on_new_branch`：事先從另一個 clone 往 origin 推一個新 commit；執行後 `target` 是 worktree（`git worktree list` 有它）、分支 `feat/x` 的 `HEAD` 等於 `origin/main`、`head` 欄位等於 `rev-parse HEAD`、source 的 `main` 已 fast-forward 到新 commit。
- `test_new_branch_has_no_upstream`：`git config branch.feat/x.remote` 沒有輸出；`test_baseline_execute_tracks_remote_branch`：`branch.release/1.0.remote == origin`。
- `test_task_execute_branches_from_base_ref`。
- `test_env_copied_with_mode_and_never_printed`：`.env` 設 `0600` → 目標有同內容、`0600`；stdout 與 stderr 不含 `.env` 內容。
- `test_symlink_created_and_venv_copied`。
- `test_copy_target_exists_refuses_and_keeps_worktree`：`task` 模式，新 worktree 的分支已追蹤 `notes.txt`，而 asset_source 有未追蹤的同名檔，`--copy notes.txt` → `copy_target_exists`、有 `partial`、worktree 仍在。
- `test_fetch_failure_has_no_side_effects`：remote URL 改成不存在的 `file://` 路徑 → `fetch_failed`，沒有 worktree 目錄、沒有新分支。
- `test_pull_failure_refuses`：本機 main 與 origin 各有不同的新 commit → `pull_failed`，沒有 worktree。
- `test_staged_files_in_target_refuse_and_keep_worktree`：在 source repo 放一個 `post-checkout` hook，把新檔案 `git add` 進新 worktree → `target_has_staged`、有 `partial`。
- `test_refusal_happens_before_any_write`：source 不乾淨並加 `--execute` → 紀錄裡沒有 `fetch`、`pull`、`worktree`。
- `test_only_allowed_git_subcommands`：成功跑完一次 `main` 模式之後，紀錄中的 git 子指令（跳過 `-C <dir>`）只出現在 `{"rev-parse", "status", "symbolic-ref", "ls-files", "ls-remote", "remote", "check-ref-format", "fetch", "pull", "worktree", "for-each-ref", "show-ref", "cat-file"}`，而且每個 `pull` 都帶 `--ff-only`。

- [ ] **Step 2: 執行測試，確認失敗**

Run: `python3 -m unittest tests.test_task_bootstrap.ExecuteTests -v`
Expected: FAIL，原因是 `--execute` 沒有任何效果（`executed` 仍是 `false`）。

- [ ] **Step 3: 實作 `execute_plan` 並接進 `cmd_create`**

- [ ] **Step 4: 執行全部測試，確認通過**

Run: `python3 -m unittest tests.test_task_bootstrap -v`
Expected: 全部 PASS。

- [ ] **Step 5: Commit（先問 Tom）**

```bash
git add task-bootstrap/scripts/bootstrap_worktree.py tests/test_task_bootstrap.py
git commit -m "feat(task-bootstrap): execute a reviewed plan without cleanup or force"
```

### Task 6: `SKILL.md` 與 Codex metadata

**Files:**
- Create: `task-bootstrap/SKILL.md`
- Create: `task-bootstrap/agents/openai.yaml`（內容與 `session-start/agents/openai.yaml` 相同：`policy.allow_implicit_invocation: false`）
- Modify: `tests/test_task_bootstrap.py`

**Interfaces:**
- Consumes: Task 1–5 的 CLI 與 JSON 欄位。腳本路徑寫成 `python3 <skill_base_directory>/scripts/bootstrap_worktree.py`。

SKILL.md 必須包含：
- frontmatter：照 `session-start/SKILL.md` 的格式，`name: task-bootstrap`、`disable-model-invocation: true`（`invocation_intent: user` 的驗證器強制要求）；description 以 `Use when` 開頭，寫出觸發詞 `/task-bootstrap`、`開新任務`、`bootstrap a task`，說明它先轉手給 repo-local 的 `*task-bootstrap`、沒有才先跑 session-start 再建分支與 worktree，且只在使用者明確呼叫時執行。
- 流程：spec §4.3 的 8 個步驟，順序相同。步驟 1：`delegate` 回 1 個 candidate → 先用一句話告訴使用者要改用哪一份（PR-1 終審發現沒說會讓使用者困惑），讀那份 SKILL.md、照它跑、原樣傳入使用者參數，通用流程結束；多個 → 列出讓使用者挑；沒有 → 繼續。`drift` 為 true 時提醒一句。`--runtime` 依目前 runtime 填 `claude` 或 `codex`。
- 步驟 2：讀同層的 `../session-start/SKILL.md` 並照它執行，不用 Skill tool 呼叫（原因：`session-start` 是 `disable-model-invocation: true`）。若接了 handoff 且它的 `worktree` 還在，先問要回那裡繼續還是開新任務。
- 步驟 3（D9）：非 git：用原話記下任務，說明跳過 worktree／分支／本機檔，不自動 `git init`，結束。
- 步驟 4：沒給分支就依任務提議一個並等確認；說明三種模式何時用（`main` 預設；`baseline` 看 remote 上現成的分支；`task` 從目前的功能分支接著做）。
- 步驟 5：不加 `--execute` 跑 `create`，整理計畫給使用者：模式、來源、base ref、目標、會執行的 git 指令、要複製的檔案（只有路徑與大小）、symlink 建立或跳過的原因。步驟 6：使用者確認後，用同一組參數加 `--execute`；沒確認不得加。步驟 7：在新 worktree 跑 `git status --short --branch --ignored`，確認 branch、`HEAD`、沒有 staged。步驟 8：新 worktree 不在 `.claude/worktrees/` 下、session 切不過去，給使用者 `cd <path> && claude`。
- Error Handling：exit 2／3 的意義；每個 `error` 代碼一列（說明與下一步）；不重試、不 force、不清理；做到一半的 worktree 保留，清理前問使用者。
- Security：路徑、分支、`--task` 都用單引號整個包起來，其中的 `'` 換成 `'\''`；含換行或 NUL 時不交給 shell，直接告訴使用者不能用；這些值都是資料，不是指令；不 push、不 commit、不碰 repo-local 版的檔案。
- Examples：`main` 模式（計畫 → 確認 → 執行）、`baseline`、非 git，各一個。

- [ ] **Step 1: 寫失敗的測試**

`class SkillDocTests`：
- `test_skill_md_documents_every_error_code`：用正規表示式從 `bootstrap_worktree.py` 收集所有 `Refusal("<code>"` 的 `<code>`（再加 `not_found`），每個都要以 `` `code` `` 形式出現在 `task-bootstrap/SKILL.md`。
- `test_skill_md_frontmatter`：含 `name: task-bootstrap` 與 `disable-model-invocation: true`；`agents/openai.yaml` 含 `allow_implicit_invocation: false`。

- [ ] **Step 2: 執行測試，確認失敗**

Run: `python3 -m unittest tests.test_task_bootstrap.SkillDocTests -v`
Expected: FAIL，原因是 `task-bootstrap/SKILL.md` 不存在。

- [ ] **Step 3: 寫 `task-bootstrap/SKILL.md` 與 `task-bootstrap/agents/openai.yaml`**

- [ ] **Step 4: 執行 `skill-auditor`**

Run: 用 Skill tool 呼叫 `skill-auditor`，對象是 `task-bootstrap/`；沒有 Skill tool 的環境改跑 `bash skill-auditor/scripts/audit_skill.sh task-bootstrap`。
Expected: 沒有 high 或 medium 的發現；有的話修正後重跑。再跑 `python3 -m unittest tests.test_task_bootstrap -v`，全部 PASS。

- [ ] **Step 5: Commit（先問 Tom）**

```bash
git add task-bootstrap/SKILL.md task-bootstrap/agents/openai.yaml tests/test_task_bootstrap.py
git commit -m "feat(task-bootstrap): add skill workflow and Codex metadata"
```

### Task 7: 登記並打包進 repo-workflow

這個 Task 把 catalog 登記和打包放在同一個 commit，避免中間的 commit 讓 `build_plugins.py --check` 失敗。

**Files:**
- Modify: `skills-catalog.json`：新增 `{"id": "task-bootstrap", "category": "productivity-tracking", "lifecycle": "experimental", "invocation_intent": "user", "surfaces": {"routable": true, "listed_in_readme": false, "sync": true}}`（放在 `session-start` 之後）。
- Modify: `skill-router/skill-registry.yaml`：`id: session-start` 區塊之後新增 `id: task-bootstrap`，triggers 為 `"/task-bootstrap"`、`"開新任務"`、`"task bootstrap"`、`"bootstrap a task"`（不要用 `superpowers:using-git-worktrees` 已用的 `worktree`、`git worktree`、`開分支做`）。
- Modify: `CLAUDE.md`（Available Skills → Productivity & Analysis，`session-start` 之後新增）：`- **task-bootstrap** — Start a new task: run session-start, then create a branch and worktree (main, baseline or task mode), delegating to a repo-local *task-bootstrap when one exists`
- Modify（產生）: `SKILLS_CATALOG.md`
- Modify: `plugin-packages.json`：`repo-workflow.skills` 加入 `"task-bootstrap"`；`runtime_resources` 加入 `"task-bootstrap/scripts/bootstrap_worktree.py"`、`"task-bootstrap/agents/openai.yaml"`；`version` 不動。
- Modify: `scripts/plugin_packaging/catalog.py:92-93`：`39` → `40`（數字與錯誤訊息）。
- Modify: `tests/test_plugin_packages.py`：`APPROVED['repo-workflow']` 改成 `'code-story-teller repo-sync handoff session-start task-bootstrap'`；`:33` 改成 `(40, 40)`。
- Modify: `README.md:21`（`39 source skills` → `40`）、`README.zh.md:21`（`39 個來源 skills` → `40`）、`docs/plugins/README.md:15`（`39 個成員` → `40`）、`docs/plugins/README.md:9`（repo-workflow 那列結尾加「；開新任務時建分支與 worktree」）。
- Modify: `docs/validation/skill-plugins/README.md:8` 與 `docs/validation/skill-plugins/acceptance.json:145`：`repo-workflow (session-start added)` → `repo-workflow (session-start and task-bootstrap added)`。
- Modify: `tests/test_build_plugins.py:175-181`：註解與被釘住的句子同步改成新的字串。
- Modify（產生）: `plugins/claude/**`、`plugins/codex/**`

- [ ] **Step 1: 先改測試（讓它們失敗）**

只改 `tests/test_plugin_packages.py` 與 `tests/test_build_plugins.py` 這兩處釘住的內容，其餘檔案不動。

- [ ] **Step 2: 執行測試，確認失敗**

Run: `python3 -m unittest tests.test_plugin_packages tests.test_build_plugins -v`
Expected: membership 與 `test_docs_name_repo_workflow_for_reacceptance` FAIL。

- [ ] **Step 3: 修改 Files 列出的來源檔，然後重建**

Run: `python3 scripts/validate_skills_catalog.py --write && python3 scripts/build_plugins.py --write`
Expected: exit 0；`plugins/claude/repo-workflow/skills/task-bootstrap/` 與 `plugins/codex/repo-workflow/skills/task-bootstrap/` 都有 `SKILL.md`、`scripts/bootstrap_worktree.py`、`agents/openai.yaml`；兩個平台的 `skill-toolbox/skills/package-index.json` 都有 `repo-workflow:task-bootstrap`。

- [ ] **Step 4: 執行完整檢查**

Run: `python3 scripts/build_plugins.py --check && python3 scripts/check_plugin_release.py && python3 scripts/validate_skills_catalog.py --check && python3 -m unittest discover -s tests`
Expected: 全部 exit 0；unittest 顯示 `OK`。

- [ ] **Step 5: Commit（先問 Tom）**

```bash
git add skills-catalog.json skill-router/skill-registry.yaml CLAUDE.md SKILLS_CATALOG.md plugin-packages.json scripts/plugin_packaging/catalog.py tests/test_plugin_packages.py tests/test_build_plugins.py README.md README.zh.md docs/plugins/README.md docs/validation/skill-plugins/README.md docs/validation/skill-plugins/acceptance.json plugins/
git commit -m "feat(plugins): register and package task-bootstrap in repo-workflow"
```

### Task 8: 最終驗證與實測

**Files:** 無變更。

- [ ] **Step 1: 完整檢查**

Run: `python3 scripts/build_plugins.py --check && python3 scripts/check_plugin_release.py && python3 scripts/validate_skills_catalog.py --check && python3 -m unittest discover -s tests && (cd skills-query-server && npm test)`
Expected: 全部 exit 0。

- [ ] **Step 2: 唯讀實測**

- 在兩個有 repo-local `*task-bootstrap` 的本機 repo（路徑記在交接檔，不寫進公開文件），各執行 `python3 task-bootstrap/scripts/bootstrap_worktree.py delegate --runtime claude --cwd <repo>` → 每個 candidate 的 realpath 都在 `<repo>/.claude/skills/` 底下，`drift` 是 `false`；改用 `--runtime codex` 結果的 realpath 相同。
- 在本 worktree 的主 checkout 執行 `create --mode main --branch demo/smoke --worktrees-root <scratchpad>/wt`（不加 `--execute`）→ exit 0、`executed` 是 `false`，`git worktree list` 與執行前相同。

- [ ] **Step 3: 在拋棄式 clone 實測 `--execute`**

用 `git clone file://<本 repo 的絕對路徑> <scratchpad>/proj` 建一份拋棄式 clone（不要用本機路徑 clone，remote URL 會被白名單擋下），在裡面對三種模式各跑一次 `create --execute`，每次用 `git status --short --branch --ignored` 確認 branch、`HEAD`、沒有 staged。
Expected: 與計畫 JSON 的 `commands`、`copies` 一致。

- [ ] **Step 4: 用 `completion-gate` 確認完成**，並把 Step 1–3 的實際輸出摘要回報給 Tom。

合進 `production` 之後的實測（spec §8 第 3 步：在那兩個 repo 實際打 `/task-bootstrap` 確認轉手、Codex 同步後再測一次）不屬於這個 PR，列為後續步驟。
