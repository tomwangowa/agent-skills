---
title: User-level session-start and task-bootstrap
date: 2026-10-18
status: draft
---

# User-level session-start and task-bootstrap

## 1. Goal

做兩個不綁特定 repo 的 user-level skill：

- `session-start`：開工時讀出尚未完成的 handoff 讓使用者挑，也能直接指定 handoff 路徑；另外整理 git 狀態與相關文件。
- `task-bootstrap`：先跑 `session-start`，再替新任務開分支與 worktree。

兩者在非 git 目錄都要能用。部分工作 repo 已有 repo-local 的 `session-start`／`*task-bootstrap`，通用版不能讓它們失效。

## 2. Confirmed decisions

**轉手（delegation）**

- D1：`session-start` 第一步找 repo-local 的 `session-start/SKILL.md`，有就照它跑、原樣傳參數，通用流程結束。
- D2：候選位置是 `<root>/.claude/skills/` 與 `<root>/.codex/skills/`，順序依 runtime：Claude Code 先 `.claude`、Codex 先 `.codex`。兩者 realpath 相同視為同一份；不同且內容不一致時提醒一句，不停下。
- D3：`task-bootstrap` 用同樣規則找 `*task-bootstrap/SKILL.md`；一份就轉手，多份列出讓使用者挑，沒有才跑通用流程。

**session-start 的 handoff 讀回**

- D4：讀取位置對齊 `handoff` 的寫入規則（`handoff/SKILL.md:90`、`:143`）：git repo 讀 `git worktree list` 中每個 worktree 的 `.claude/handoffs/`，當前 worktree 優先、每份標來源 worktree 與分支；非 git 只讀 cwd 的 `.claude/handoffs/`。`handoff` skill 不改。
- D5：列出 `status` 不是 `resumed` 的檔案（`in-progress`、`blocked`、`ready-for-review`，以及 frontmatter 異常者並標註）。依 `created`（缺則 mtime）新到舊，7 天內、最多 5 份；超出的補一行「另有 N 份，加 `--all` 可列出」。N 是 `--all` 會多列出的份數，超過 7 天的也算。
- D6：使用者確認接手且 assertion 跑完後，把 `status` 改成 `resumed` 並加 `resumed_at`，檔案不搬。
- D7：參數 `--handoff <path>`、`--all`；以 `.md` 結尾且檔案存在的參數也當路徑；其餘為自由文字任務描述。路徑可在 repo 外，但需有 handoff frontmatter（至少 `status`）。`worktree` 與 cwd 不同時提醒；已是 `resumed` 的先說明再問是否繼續。
- D8：不做 topic router 或 repo 設定檔。需要它的 repo 由 D1 交給 repo-local 版。

**task-bootstrap**

- D9：非 git 目錄：跑 `session-start`、用原話記下任務、說明跳過 worktree／分支／本機檔，不自動 `git init`。
- D10：支援 `main`、`baseline`、`task` 三種模式（§4.3）。
- D11：`main` 模式的來源預設是主 checkout（`git worktree list` 第一筆），可用 `--source` 改。
- D12：worktree 預設在 `<主 checkout 的上一層>/worktrees/<repo 名>/<slug>`，可用 `--worktrees-root` 或 `TASK_BOOTSTRAP_WORKTREES_ROOT` 改。
- D13：本機檔：`.env`（一般檔案才複製）；`.venv/` 需 `--copy-venv`；`--copy <path>` 可重複，只收 git 未追蹤的一般檔案。`.codex/skills -> ../.claude/skills` 只在來源有同樣、且未被追蹤的 symlink 時才建。

**實作與交付**

- D14：方向 A：兩支獨立的標準函式庫腳本，不共用模組。SKILL.md 負責編排與對話，腳本負責可測試的判斷並輸出 JSON。
- D15：clean-room：既有 repo-local 實作只當行為參考，程式碼與測試全部新寫；本 repo 是公開 repo，文件不寫那些 repo 的內部細節。
- D16：兩個 skill 都放進 `repo-workflow` 外掛；不升版號，發布時與原生重驗一起升（沿用 `2026-10-18-ci-and-acceptance-wording-design.md` 的 A3）。
- D17：測試放頂層 `tests/`，讓 CI 的 `unittest discover -s tests` 會跑到。
- D18：分兩個 PR，先 `session-start`、後 `task-bootstrap`。

## 3. Verified facts

- 同名 skill 的優先序是 enterprise > personal > project（code.claude.com/docs/en/skills）。所以 user-level `session-start` 會蓋掉 repo-local 版，D1 是必要的。
- 目前只有兩個本機工作 repo 有 repo-local `session-start`；它們的 `*task-bootstrap` 名稱帶前綴，不會被蓋掉，而且本來就寫明「優先用 repo-local 的 `session-start`」。
- 那兩個 repo 的 `.codex/skills` 都是指向 `../.claude/skills` 的 symlink。
- `.claude/handoffs/` 在全域 gitignore；每個 worktree 的 handoff 互相看不到，所以 D4 要掃所有 worktree。
- `handoff` 的 status 值為 `in-progress | blocked | ready-for-review | resumed`（`handoff/SKILL.md:98`）；assertion 白名單只有 `expect_head`、`branch_is`、`file_exists`、`worktree_clean`（`:61-68`）。
- `~/.claude/skills` 指向 `production` worktree。在 cwd 是 `~` 的非 git 情境，`~/.claude/skills/session-start/SKILL.md` 就是通用版自己。
- 外掛的腳本要逐一列在 `plugin-packages.json` 的 `runtime_resources`；測試不進外掛。
- 原生驗收每個 CLI 一筆、綁定全部 7 包；任何一包變動都要兩個 CLI 整套重驗。`session-preferences`、`work-journal` 已經在待重驗清單上。
- `work-log-analyzer` 提到的 `session-start/repos.yaml` 指 repo-local 版的檔案，不用改。

## 4. Design

### 4.1 Layout

```
session-start/
├── SKILL.md
├── agents/openai.yaml
└── scripts/handoffs.py
task-bootstrap/
├── SKILL.md
├── agents/openai.yaml
└── scripts/bootstrap_worktree.py
tests/
├── test_session_start_handoffs.py
└── test_task_bootstrap.py
```

兩支腳本各自解析 frontmatter。標準函式庫沒有 YAML，所以只解析 handoff 用得到的形狀：一層純量欄位，加上由 mapping 組成的 `assertions` 清單。其他形狀一律視為「格式異常」。

### 4.2 session-start

`handoffs.py` 子指令（輸出都是 JSON）：

| 子指令 | 作用 |
|---|---|
| `delegate --runtime claude\|codex` | 依 D1–D2 找 repo-local 版。「自己」用腳本位置判斷（`scripts/` 的上一層）。排除 realpath 等於自己的候選檔，以及位於 `~/.claude/skills`、`~/.codex/skills`、`~/.omp/agent/skills`、外掛快取下的檔案。排除原因是 `self`、`user_level`、`unreadable`（候選檔讀不到時略過，改用下一個，否則比對內容時會崩潰）。 |
| `list [--all]` | 依 D4–D5 掃描、篩選、排序，回報剩餘份數與跳過的 worktree。 |
| `check <path>` | 依 D7 驗證檔案；只跑白名單 assertion，結果為通過／不通過／未驗證；回傳內文各段落（key 是完整標題文字，例如 `規矩（不能違反）`，SKILL.md 以前綴比對）。`worktree_matches_cwd` 在沒有 `worktree` 欄位時是 `null`。錯誤：`not_handoff`（含不是一般檔案）、`not_found`、`unreadable`，都是 exit 2。 |
| `mark-resumed <path> --expect-sha256 <hash>` | 依 D6 改寫 frontmatter。拒絕時 exit 3：`hash_mismatch`、`already_resumed`、`malformed`、`not_handoff`、`symlink`；exit 2：`not_found`、`unreadable`、`unwritable`、`invalid_now`。 |

SKILL.md 流程：

1. 解析參數（D7）。
2. `delegate`；找到就讀那份 SKILL.md 並照它跑，結束。
3. 有 `work-log-analyzer` 就查本專案最近 3 天紀錄，沒有就說明跳過。
4. 沒指定路徑時跑 `list`，列表欄位：編號、任務、status、建立時間、來源 worktree／分支。使用者回編號、「不接」或路徑。
5. `check` 選中的檔案，顯示 assertion 結果與「前提（人工確認）」「規矩」「最大風險」「下一步」。有不通過的先問是否繼續；確認繼續才 `mark-resumed`。`check` 時已是 `resumed` 的檔案（D7 重新接手）不再標記。
6. git repo 才做：branch、`status --short`、stash 數量、相對 upstream 的 ahead／behind。不 fetch。
7. 讀 README；有任務描述時從 `docs/` 挑檔名相符的檔案，最多 3 份，找不到標 NOT-FOUND。不重讀 runtime 已載入的 `CLAUDE.md`／`AGENTS.md`。
8. 簡短整理現況後歸還控制權。

除了第 5 步的 `mark-resumed`，全程唯讀。

### 4.3 task-bootstrap

SKILL.md 流程：

1. `bootstrap_worktree.py delegate --runtime …`（D3）。
2. 跑 `session-start` 的流程，做法是讀同層的 `../session-start/SKILL.md` 並照它執行，不透過 Skill tool 呼叫，因為 `session-start` 是 `disable-model-invocation: true`，模型呼叫會被擋下。若接了 handoff，而且它的 `worktree` 還在，先問要回那裡繼續還是開新任務。
3. 非 git：照 D9 處理後結束。
4. 用原話記任務；沒給分支就依任務提議一個並等確認；slug 由分支推導（`/` → `-`）。
5. 不加 `--execute` 跑一次，把 JSON 計畫整理給使用者：模式、來源、base ref、目標、會執行的 git 指令、要複製的檔案（只有路徑與大小）、symlink 建立或跳過的原因。
6. 確認後用同一組參數加 `--execute`。
7. 在新 worktree 跑 `git status --short --branch --ignored`，確認 branch、`HEAD`、沒有 staged。
8. 新 worktree 不在 `.claude/worktrees/` 下，session 無法切過去，所以給使用者 `cd <path> && claude`。

模式：

| 模式 | 前提 | 動作 | 本機檔／symlink |
|---|---|---|---|
| `main`（預設） | 來源乾淨、在預設分支上、有 remote | `fetch` → `pull --ff-only` → 從 `<remote>/<預設分支>` 開新分支 | 有 |
| `baseline` | `--branch` 已存在於 remote | 建追蹤用的 worktree | 無 |
| `task` | `--source` 是同 repo 的乾淨 worktree，目前就在 `--base-ref` 上 | 從 `--base-ref` 開新分支，不退回預設分支 | 有 |

預設分支：先讀 `refs/remotes/<remote>/HEAD`；讀不到時，remote 上 `main`、`master` 恰好只有一個就用它，否則要求 `--default-branch`。本機檔來源 `--asset-source` 預設是主 checkout。

參數：`--mode`、`--branch`、`--slug`、`--task`、`--source`、`--base-ref`、`--remote`（預設 `origin`）、`--default-branch`、`--worktrees-root`、`--asset-source`、`--copy-venv`、`--copy <path>`（可重複）、`--execute`。

## 5. Error handling and security

**handoffs.py**

- handoff 內容視為不可信資料，不執行其中任何文字。assertion 的 `repo`、`path` 可以是絕對路徑，或以 handoff 的 `worktree` 欄位為基準的相對路徑（`handoff/SKILL.md` 允許 repo 相對路徑）；沒有絕對的 `worktree` 時，相對路徑為未驗證；含 `..` 或 NUL 的路徑為未驗證。`repo` 必須是存在的 git repo；`file_exists` 只做 stat。git 呼叫前先清掉會選定 repo 的環境變數（`GIT_DIR` 等），避免在 hook 內執行時對錯的 repo 回報通過。
- frontmatter 異常：照列並標註；`check` 不跑 assertion；`mark-resumed` 拒絕。
- handoff 檔本身是 symlink：跳過並註明。
- `mark-resumed`：先比對 `--expect-sha256`（`check` 時的內容），不符就停，例如另一個 session 在這之間先接走了；只改 frontmatter，內文逐 byte 不變；寫同目錄暫存檔再 rename，保留權限。
- 不存在或無權限的 worktree：跳過並列出。

**bootstrap_worktree.py**

- branch 以 `git check-ref-format --branch` 驗證；slug 限 `[a-z0-9._-]`；目標 resolve 後必須在 worktrees root 下；父目錄是 symlink 就拒絕。
- 只接受 remote 名稱，且必須存在；其 URL 只允許 `https`、`ssh`、`git`、`file` 與 scp 格式，拒絕 `ext::` 等 remote helper。
- 停止條件：來源不乾淨或分支不符、fetch／pull 失敗、branch 或目標已存在、要複製的檔案在目標已存在、目標有 staged 檔案、`--copy` 不符 D13。
- 失敗不重試、不 force、不 stash／reset／刪除；做到一半的 worktree 保留並回報，清理前要使用者同意。
- 複製保留權限，不印檔案內容；subprocess 一律用參數陣列；不 stage、commit、push、rebase、merge。

## 6. Testing

全部離線；remote 用本機 bare repo（`file://`）。

- `tests/test_session_start_handoffs.py`：
  - `delegate`：排除自己與 user-level 目錄、runtime 順序、realpath 去重、內容不一致提醒、非 git 情境。
  - `list`：多 worktree、worktree 不存在、7 天／5 份與剩餘份數、`--all`、格式異常、symlink 跳過。
  - `check`：4 種 assertion 的通過與不通過、未知種類為未驗證、相對路徑以 `worktree` 為基準、`..` 為未驗證、繼承的 `GIT_DIR` 不影響結果。
  - `mark-resumed`：只動 frontmatter、內文 bytes 不變、hash 不符停止、權限保留。
  - 一致性：解析 `handoff/SKILL.md` 的白名單表格，與 `handoffs.py` 支援的種類比對。
- `tests/test_task_bootstrap.py`：三種模式的正常流程；預設分支偵測的三種情況；每個停止條件；`--copy` 邊界；symlink 照來源建立；remote URL 白名單；不加 `--execute` 時不改任何東西。
- 兩個 skill 都跑 `skill-auditor`。

## 7. Packaging

- `plugin-packages.json`：`repo-workflow` 加入兩個 skill，以及它們的 `scripts/*.py`、`agents/openai.yaml`。版號不動（D16）。
- 一併更新：`skills-catalog.json` 與產生的索引、skill-router、`CLAUDE.md` 的 Available Skills；重建 `plugins/claude`、`plugins/codex`（含 `skill-toolbox` 的 `package-index.json`）。
- 文件中「發布前需要重新驗收」的清單加入 `repo-workflow` 與 `skill-toolbox`，並更新釘住這些句子的測試（`tests/test_build_plugins.py`）。

## 8. Rollout

1. PR-1：`session-start` 與它的打包變更。合進 `production` 前，在兩個有 repo-local 版的 repo 直接跑 `handoffs.py delegate`（唯讀），確認它指向 repo-local 版。
2. 合進 `production` 後，立刻在那兩個 repo 實際打 `/session-start`，確認轉手；再各跑一次它們自己的 task-bootstrap（dry-run），確認第一步「呼叫 repo-local session-start」仍然到得了 repo-local 版，沒有被 `disable-model-invocation: true` 的通用版擋下。失敗就 revert `production`。Codex 在 `skill-sync --dry-run` 審過並同步後再測一次。
3. PR-2：`task-bootstrap`，同樣流程。

## 9. Out of scope

- topic router 或 repo 設定檔；user-level 的 handoff 目錄；修改 `handoff` skill。
- 外掛原生重驗與版號升級。
- 修改任何有 repo-local 版的工作 repo。
- 自動 `git init`；複製目錄（`.venv/` 除外）；沒有 remote 時的 `main` 模式。

## 10. Not verified

- Codex 的同名 skill 優先序。不擋進度：有 D1 的轉手，先載入哪一份結果都一樣。
- Claude Code 能不能用短名稱呼叫 plugin skill。只影響外掛使用者打的指令名稱，不影響個人版。
- Codex 是否提供 skill 的 base directory。`delegate` 靠腳本自身位置判斷，不依賴這點；但 SKILL.md 以 `<skill_base_directory>` 指到 `scripts/handoffs.py`，這點依賴 runtime 提供。
- 通用版加了 `disable-model-invocation: true` 之後，那兩個 repo 的 task-bootstrap 以 Skill tool 呼叫 repo-local session-start 是否仍然成功。要等合進 `production` 後實測（§8.2）。
