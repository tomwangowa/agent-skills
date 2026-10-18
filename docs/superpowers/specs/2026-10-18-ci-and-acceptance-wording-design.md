---
title: CI for tests and plugin integrity, and accurate acceptance wording
date: 2026-10-18
status: draft
---

# CI for tests and plugin integrity, and accurate acceptance wording

## 1. Goal

兩件事：

- **A**：`session-preferences` 與 `work-journal` 的原生驗收綁定已過期，但文件仍寫「七包通過原生驗收」。把現況說明改成準確的說法。
- **B**：repo 目前沒有 CI。#31 的問題（手改生成檔，來源與產出不一致）要靠人工 review 才發現。加一個 CI，在 PR 階段擋下這類問題。

## 2. Confirmed decisions

- A1：驗收過期先記錄，發布前再對 `session-preferences`、`work-journal` 重跑原生驗收。不新增「沿用舊驗收」的機制。
- A2：改現況說明與驗收記錄：根目錄 `README.md`、`README.zh.md`，`docs/plugins/installation.md`，`scripts/plugin_packaging/render.py:154` 的外掛 README 句子，`acceptance.json` 的 `limits`，validation README。有日期的歷史記錄 `task-8-release-validation.md` 不改。
- A3：不升版號，發布時與重新驗收一起升。在 #31 留言更正「merge 後用 `plugin update` 就能拿到新文件」。
- B1：CI 跑 `build_plugins.py --check`、`check_plugin_release.py`（不加 `--require-acceptance`）、Python 完整測試、`skills-query-server` 的 `npm test`，全部必過。
- B2：只用 macOS runner，Node 24、Python 3.12。
- B3：`prepare_server` 移除 `node_modules/.package-lock.json`，並補測試。
- B4：CI 第一次通過後設 ruleset，要求 CI 通過才能 merge 到 `main`，repo admin 可略過。
- 做法：單一 workflow、單一 job，步驟直接寫在 workflow 裡。不拆平行 job，也不另寫腳本。
- 命名：檔名 `.github/workflows/tests-and-plugin-integrity.yml`，workflow 名稱 `Tests and plugin integrity`，job 名稱 `tests-and-plugin-integrity`。required status check 比對的是 job 名稱，所以 job 不取泛用名稱。
- 順序：PR-1（CI 加 B3），merge 後設 ruleset，再從新的 `main` 開 PR-2（A2）。

## 3. Verified facts

- repo 沒有 `.github/` 目錄。repo 為 public，`main` 沒有 branch protection（`gh api .../branches/main/protection` 回 404）。
- `d738ec4`（2026-10-16）改了 `runtime/agent_skills_runtime/migration.py` 的 `_legacy()` 路徑比對，時間在 2026-10-15 原生驗收之後。這個 commit 包含在 PR #30 裡。
- `check_plugin_release.py --require-acceptance` 在 `3f674e4`（PR #30 的 merge commit）上已經失敗。不符的是 `session-preferences`、`work-journal` 在兩個 surface 上的 `native_binding`；其餘 5 包相符。
- `native_binding` 只納入 `skills`、`runtime`、`hooks`、`server`、`.claude-plugin`、`.codex-plugin`、`.mcp.json`（`scripts/plugin_packaging/verify.py:20`），根目錄的文件不在範圍內。
- 7 個包都沒有 release tag，只有 `handoff-mod-v0.2.0`。
- 只有 `plugins/{claude,codex}/work-journal/` 帶 `server/`。其中的 `node_modules/.package-lock.json` 有被 git 追蹤，也列在 `.generated-files.json`。
- npm 文件說明，`node_modules/.package-lock.json` 是 npm v7 起的 hidden lockfile，只有 npm 會讀；條件不符時 npm 會忽略它（https://docs.npmjs.com/cli/v11/configuring-npm/package-lock-json）。
- production 依賴 101 個，沒有 `os`／`cpu` 限制，也沒有 optional 依賴。bundle 裡的 `@esbuild` 是空目錄，git 不追蹤。
- `render.py:154` 寫死外掛 README 的句子：「Native acceptance passed … Remote marketplace installation and release approval remain pending.」
- 本機（macOS 26.6.2 arm64、Node 23.7.0、npm 11.2.0、Python 3.12.1）：`unittest discover -s tests` 全部通過，約 33 秒；`npm test` 通過，smoke 8/8。
- action 版本（2026-10-18 查詢，tag 指向 commit）：
  - `actions/checkout` v7.0.1：`3d3c42e5aac5ba805825da76410c181273ba90b1`
  - `actions/setup-python` v7.0.0：`5fda3b95a4ea91299a34e894583c3862153e4b97`
  - `actions/setup-node` v7.1.0：`949feb2413d6458794dcd2491c4babbbce0c15c1`

- `macos-26` label 是 macOS 26 arm64 映像（`actions/runner-images` README）。
- `test_plugin_runtime_probe.py` 用自己的 `build_probe_fixture`，不執行生成的 bundle；`stdio.integration.test.ts` 用原始碼的 `dist` 加開發用 `node_modules` symlink。目前沒有測試執行生成的 bundle。
- 兩個外掛都以 `server/launch.mjs` 啟動 server；server 從 `AGENT_SKILLS_CONFIG_DIR` 讀設定，未設定時用 `homedir()`。
- 沒有測試斷言 `render.py:154` 的舊字串。

NOT VERIFIED：

- 13 個測試檔與 `npm test` 在 runner 上用 Node 24 是否都通過。
- runner 上 `npm ci` 產出的 bundle 是否與本機 byte 一致（PR-1 自己的 CI 會回答）。
- 移除 `.package-lock.json` 後 server 是否照常執行（以生成 bundle 的 smoke 測試確認）。
- 版號不變時 `plugin update` 不會拉新文件：依據是 lesson 記錄與 #31 驗證紀錄中 `up_to_date`、雜湊不變的結果，沒有針對文件變動單獨實測。

## 4. PR-1：CI 與 bundle 決定性

### 4.1 Workflow

`.github/workflows/tests-and-plugin-integrity.yml`：

- 觸發：`pull_request`（目標 `main`）、`push` 到 `main`、`workflow_dispatch`。用 `concurrency` 取消同一 ref 上較舊的執行。
- 權限：`permissions: contents: read`，不使用 secrets。
- job `tests-and-plugin-integrity`，`runs-on: macos-26`。
- 步驟：
  1. checkout（以 SHA 釘版本，註解寫版號）
  2. setup-python，`python-version: '3.12'`
  3. setup-node，`node-version: '24'`，`cache: npm`，`cache-dependency-path: skills-query-server/package-lock.json`
  4. `npm ci`（`working-directory: skills-query-server`）
  5. `python3 scripts/build_plugins.py --check`
  6. `python3 scripts/check_plugin_release.py`
  7. `python3 -m unittest discover -s tests`
  8. `npm test`（`working-directory: skills-query-server`）

### 4.2 `prepare_server`

在 `scripts/build_plugins.py` 的 `npm ci --omit=dev` 之後，刪除 `destination / 'node_modules/.package-lock.json'`，放在刪 `.bin` 的那段旁邊，並以註解說明原因：這是 npm 專用的記錄，server 執行時不會載入。

實作後的查證（2026-10-18，分支 review）：在 `247d1e9` 上分別用 npm 11.2.0 與 11.21.1 跑 `--check`，兩者都相符，也就是「npm 版本不同，hidden lockfile 內容就不同」沒有實證。這項改動仍然保留，當作防禦性清理：生成 bundle 的 smoke 測試證明 server 不需要這個檔，拿掉它可以讓發布內容少一個 npm 專用的檔案。

`--write` 後，只有兩份 `work-journal` 的 `server/node_modules/.package-lock.json` 與 `.generated-files.json` 會變動。

### 4.3 測試

- `tests/test_build_plugins.py` 新增斷言：生成的 `work-journal` server 裡沒有 `node_modules/.package-lock.json`。先在未修改的程式碼上確認它失敗，改完再看它通過。
- 在 `stdio.integration.test.ts` 補一個測試：把 `plugins/<surface>/work-journal/server` 複製到暫存 fixture，以 `launch.mjs` 啟動，`AGENT_SKILLS_CONFIG_DIR` 指向 fixture，跑完整的 smoke round trip。這是唯一執行生成 bundle 的測試，也證明移除 `.package-lock.json` 後 server 照常執行，而且不會碰到使用者的真實資料。

### 4.4 對驗收的影響

`server/` 在 `native_binding` 範圍內，`work-journal` 的綁定會改變。它本來就已經過期，所以實質影響為零。PR 說明要寫明這一點。

## 5. Ruleset

PR-1 merge、CI 在 `main` 上通過之後：

- 用 `gh api` 在 `main` 建 ruleset，required status check 為 `tests-and-plugin-integrity`，bypass 對象為 repo admin。
- 送出前先把 JSON 給使用者確認。送出後讀回來核對。

## 6. PR-2：驗收說法

從新的 `main` 開分支。

- 改來源，再用 `--write` 重建：
  - `docs/plugins/installation.md` 第 3 行：說明 2026-10-15 的原生驗收涵蓋七包；`session-preferences` 與 `work-journal` 之後有修改，發布前需重新驗收。
  - `render.py:154`：外掛 README 句子改成同樣的意思，遠端措辭與 #31 一致（Claude Code 的 GitHub marketplace 已驗證，Codex 的遠端流程尚未測試）。
- 直接修改：`README.md`、`README.zh.md` 第 21 行，validation README，`acceptance.json` 的 `limits` 新增一條。這一條寫明過期原因（`d738ec4` 與 PR-1 的 bundle 變動）與發布前重跑的要求。
- PR-2 開出時，同時在 #31 留言更正更新說明。留言內容先給使用者確認。

## 7. Error handling

- PR-1 的 CI 失敗：先用 systematic-debugging 判斷是環境差異（Node 24、runner 映像），還是 bundle 不是決定性的，只修根因。不使用 `continue-on-error`，也不移除檢查。
- runner 上 `--check` 回報 drift：在 CI 加一步列出差異的檔案名稱（做法同 `staging` 逐檔比對），再根據實際差異處理。

## 8. Out of scope

- 升版號、重跑原生驗收：發布時再做。
- Linux runner；在 CI 跑 `--require-acceptance`。
- `docs/plugins/superpowers-compatibility.md:29` 的遠端措辭：它描述的是 session 內的行為，遠端檢查沒有涵蓋。
- `render.py:90` 的權限正規化：CI 使用 git checkout，權限正確，問題只發生在本機。

## 9. Verification

- PR-1：本機跑 `--check`、`check_plugin_release.py`、完整 `unittest`、`npm test`；PR 上的 `tests-and-plugin-integrity` 通過；新斷言先失敗後通過。
- Ruleset：`gh api` 讀回的設定與送出的一致。
- PR-2：CI 通過；在 `README.md`、`README.zh.md`、`docs/plugins/`、`plugins/` 下 grep `七包已在`、`Native acceptance passed`、`完成原生驗收`、`Remote marketplace installation and release approval remain pending`，結果為零；`task-8-release-validation.md` 沒有變動。
