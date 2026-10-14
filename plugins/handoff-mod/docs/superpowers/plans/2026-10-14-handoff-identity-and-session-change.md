# 交接的識別與「本 session 有變化」實作計畫

> **給執行者：** 必讀子技能：`superpowers:subagent-driven-development`（建議）或 `superpowers:executing-plans`，逐任務執行。步驟用 `- [ ]` 追蹤。

**目標：** handoff-mod 0.2.0。同一份交接的副本只算一筆（D20）；狀態讀取時退回舊的 path key（D21）、寫入時新舊 key 都寫（D22）；結束筆記只在這個 session 造成變化時才寫（D23）；60% 提示到門檻就問（D24）。

**架構：** 新增兩個純函式模組：`hooks/identity.js`（識別、合併副本、key 清單、挑最新紀錄）與 `hooks/snapshot.js`（解析 `git status -z`、快照、比對）。`register.js` 只接線：清單合併後再查狀態，寫入走 `writeState`，快照存在既有的 `last:<sessionId>` 紀錄的 `baseline` 欄位，結束時用 `sessionChanged` 取代 dirty 判斷。`claim.js` 改收一組 key，`handoff-file.js` 讓已處理的檔案帶 `meta`（仍是 `ok: false`）。

**技術：** Claude Code mod，純 ES modules，測試用 `claude-code/testing`（`claude plugin test .` 會跑整個資料夾，不能只跑單一檔案）。

**規格：** [交接的識別與「本 session 有變化」](../specs/2026-10-14-handoff-identity-and-session-change-design.md)（D20 至 D24）。**分支：** `feat/handoff-identity`（從 `main` 的 `dcf71dc` 開出）。

**commit 規則：** 每個「Commit」步驟都要先依使用者的 pre-commit 規則判斷風險（L0／L1／L2），並**取得 Tom 同意後**才執行 `git commit`。訊息照 Conventional Commits，結尾加 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`。

所有指令都在 `plugins/handoff-mod/` 底下執行，除非另有註明。

---

## 檔案結構

| 檔案 | 動作 | 負責 |
| --- | --- | --- |
| `hooks/identity.js` | 新增 | `handoffKey`、`mergeCopies`、`stateKeys`、`claimKeys`、`newestState` |
| `hooks/snapshot.js` | 新增 | `BASELINE_MAX`、`parseStatusZ`、`takeBaseline`、`hasNewEntry`、`changedSince` |
| `hooks/handoff-file.js` | 修改 `parseHandoff` | 已處理的檔案回 `{ok: false, reason: 'status', meta, fields}` |
| `hooks/claim.js` | 修改 `tryClaim` | 收 `keys`，任一被佔用就擋，全部都寫 |
| `hooks/register.js` | 修改 | `readHandoffs`、`buildList`、`writeState`、`resume`、`abandon`、`checkThreshold`、`recordRequest`、`statEntries`、`takeSessionBaseline`、`sessionChanged`、`writeEndNote` |
| `tests/identity.test.ts`、`tests/snapshot.test.ts` | 新增 | 純模組測試 |
| `tests/handoff-file.test.ts`、`tests/claim.test.ts` | 修改 | 新行為 |
| `tests/world.ts` | 修改 | `gitDelays`：只延遲指定的 git 指令 |
| `tests/register.test.ts` | 修改 | D20 至 D24 的接線測試；改寫 4 個依賴舊行為的測試 |
| `README.md`、`README-en.md`、`CHANGELOG.md`（新）、`docs/implementation-results.md`、`docs/poc-results.md`、設計主檔 | 修改 | 文件 |
| `.claude-plugin/plugin.json`、`package.json` | 修改 | 版號 0.2.0 |
| `~/Development/harness/handoff-poc/` | 暫時新增（repo 外），Task 2 結束後刪除 | PoC 用的拋棄式 plugin |

---

### Task 0：分支、baseline、spec commit

**Files:** 無程式變更。

- [ ] **Step 1：開分支**（在 repo 根目錄 `~/Development/harness/agent-skills`）

```bash
git switch main && git status --short
git switch -c feat/handoff-identity
```

預期：`git status --short` 只有 `?? GEMINI.md` 與 `?? plugins/handoff-mod/docs/superpowers/specs/2026-10-14-handoff-identity-and-session-change-design.md`、`?? plugins/handoff-mod/docs/superpowers/plans/2026-10-14-handoff-identity-and-session-change.md`。有其他變更就停下來回報。

- [ ] **Step 2：baseline 測試與驗證**

```bash
cd plugins/handoff-mod
claude plugin test . 2>&1 | tail -3
claude plugin validate --strict . 2>&1 | tail -1
```

預期：`183 pass`、`0 fail`、`✔ Validation passed`。乾淨分支上就失敗的話，先回報 Tom，不能算到這次的改動上。

- [ ] **Step 3：Commit spec 與計畫**（先取得 Tom 同意）

```bash
git add docs/superpowers/specs/2026-10-14-handoff-identity-and-session-change-design.md docs/superpowers/plans/2026-10-14-handoff-identity-and-session-change.md
git commit -m "docs(handoff-mod): add identity and session-change design and plan"
```

---

### Task 1：PoC plugin

規格要求實作前先確認四件事。這個 plugin 放在 repo 外，Task 2 結束就刪除，不 commit。

**Files:**
- Create: `~/Development/harness/handoff-poc/.claude-plugin/plugin.json`
- Create: `~/Development/harness/handoff-poc/package.json`
- Create: `~/Development/harness/handoff-poc/hooks/hooks.json`
- Create: `~/Development/harness/handoff-poc/hooks/register.js`

- [ ] **Step 1：寫 `plugin.json`**

```json
{
  "name": "handoff-poc",
  "version": "0.0.1",
  "description": "Throwaway PoC for handoff-mod 0.2.0: store concurrency, end-time cost, submit ordering, session id after /clear."
}
```

- [ ] **Step 2：寫 `package.json`**

```json
{
  "name": "handoff-poc",
  "version": "0.0.1",
  "private": true,
  "type": "module"
}
```

- [ ] **Step 3：寫 `hooks/hooks.json`**

```json
{
  "modules": ["./register.js"]
}
```

- [ ] **Step 4：寫 `hooks/register.js`**

```js
/*
 * Throwaway PoC for handoff-mod 0.2.0. Every finding is written to this plugin's own $.store under `poc:` and shown by
 * /poc-report, because session.end output cannot be seen. Delete this folder after the PoC.
 */
const KEY = 'poc:';
const STATUS_ARGS = ['status', '--porcelain', '-z', '--untracked-files=all'];
const pause = ($, ms) => new Promise((resolve) => $.clock.after(ms, resolve));

async function toplevel($) {
  const run = await $.process.run(['git', 'rev-parse', '--show-toplevel'], {timeoutMs: 5000});
  return String(run.stdout ?? '').trim();
}

async function statusEntries($) {
  const run = await $.process.run(['git', ...STATUS_ARGS], {timeoutMs: 5000});
  const fields = String(run.stdout ?? '').split('\0');
  const entries = [];
  for (let i = 0; i < fields.length; i++) {
    if (fields[i].length < 4) continue;
    const code = fields[i].slice(0, 2);
    entries.push({code, path: fields[i].slice(3)});
    if (/[RC]/.test(code)) i++;
  }
  return {exitCode: run.exitCode, entries};
}

/** stat up to 50 entries the way 0.2.0 will; returns how many failed. */
async function statAll($, root, entries) {
  let failed = 0;
  for (const entry of entries.slice(0, 50)) {
    if (entry.code.includes('D')) continue;
    try { await $.fs.stat(`${root}/${entry.path}`); } catch { failed++; }
  }
  return failed;
}

async function remember($, key, value) {
  try { await $.store.set(`${KEY}${key}`, value); } catch { /* PoC only */ }
}

async function appendId($, value) {
  try {
    const ids = (await $.store.get(`${KEY}ids`)) ?? [];
    await $.store.set(`${KEY}ids`, [...ids, value]);
  } catch { /* PoC only */ }
}

export function register(on) {
  on('session.start', async ($, e, next) => {
    const result = await next(e);
    try {
      for (const name of ['poc-burst', 'poc-count', 'poc-report', 'poc-clean']) await $.command.register({name, description: `handoff PoC: ${name}`});
    } catch { /* PoC only */ }
    await appendId($, {event: 'session.start', id: await $.session.id(), at: await $.clock.now()});
    return result;
  });

  // PoC 4: does /clear give the session a new id?
  on('classic.SessionStart', async ($, e, next) => {
    const result = await next(e);
    await appendId($, {event: `classic.SessionStart:${e.source}`, id: await $.session.id(), hookSessionId: e.session_id, at: await $.clock.now()});
    return result;
  });

  // PoC 3: does the host wait for this hook before the turn starts? The 8 s pause makes the answer obvious.
  on('prompt.submit', async ($, e, next) => {
    const result = await next(e);
    try {
      const text = String(result.text ?? e.text ?? '');
      if ('drop' in result || text.startsWith('/')) return result;
      const sid = await $.session.id();
      if (await $.store.get(`${KEY}submit:${sid}`)) return result;
      const startAt = await $.clock.now();
      const status = await statusEntries($);
      await statAll($, await toplevel($), status.entries);
      // What 0.2.0's baseline will cost at the first prompt, measured before the artificial pause.
      const gitStatMs = (await $.clock.now()) - startAt;
      await pause($, 8000);
      await remember($, `submit:${sid}`, {startAt, gitStatMs, doneAt: await $.clock.now(), entries: status.entries.length});
    } catch (error) {
      await remember($, 'submit:error', String(error?.message ?? error));
    }
    return result;
  });

  // PoC 3: when did the first tool call of the session happen? Observe only; the call goes on unchanged.
  on('tool.call', async ($, e, next) => {
    try {
      const sid = await $.session.id();
      if (!(await $.store.get(`${KEY}tool:${sid}`))) await remember($, `tool:${sid}`, {tool: e.tool, at: await $.clock.now()});
    } catch { /* PoC only */ }
    return next(e);
  });

  // PoC 2: what git status -z --untracked-files=all and 50 stats cost at session end, and how much budget there is.
  on('session.end', async ($, e, next) => {
    try {
      const remainingMs = Number(next.budget?.remainingMs);
      const t0 = await $.clock.now();
      const root = await toplevel($);
      const status = await statusEntries($);
      const t1 = await $.clock.now();
      const statFailed = await statAll($, root, status.entries);
      const t2 = await $.clock.now();
      await remember($, `end:${e.sessionId}`, {cwd: root, remainingMs, gitMs: t1 - t0, statMs: t2 - t1, entries: status.entries.length, statFailed, at: t2});
    } catch (error) {
      await remember($, `end:${e.sessionId}`, {error: String(error?.message ?? error)});
    }
    return next(e);
  });

  // PoC 1: two sessions write 300 keys each at the same time; do both sets survive?
  on('command.run', {command: 'poc-burst'}, async ($, e) => {
    try {
      const tag = String(e.args ?? '').trim() || 'X';
      for (let i = 0; i < 300; i++) {
        await $.store.set(`${KEY}burst:${tag}:${i}`, i);
        await pause($, 10);
      }
      $.ui.log(`poc-burst ${tag}: wrote 300 keys`);
    } catch (error) {
      $.ui.log(`poc-burst failed: ${String(error?.message ?? error)}`);
    }
    return {};
  });

  on('command.run', {command: 'poc-count'}, async ($) => {
    try {
      const counts = {};
      for (const key of await $.store.keys()) {
        if (!key.startsWith(`${KEY}burst:`)) continue;
        const tag = key.split(':')[2];
        counts[tag] = (counts[tag] ?? 0) + 1;
      }
      $.ui.log(`poc-count: ${JSON.stringify(counts)}`);
    } catch (error) {
      $.ui.log(`poc-count failed: ${String(error?.message ?? error)}`);
    }
    return {};
  });

  on('command.run', {command: 'poc-report'}, async ($) => {
    try {
      for (const key of await $.store.keys()) {
        if (key.startsWith(KEY) && !key.startsWith(`${KEY}burst:`)) $.ui.log(`${key} = ${JSON.stringify(await $.store.get(key))}`);
      }
    } catch (error) {
      $.ui.log(`poc-report failed: ${String(error?.message ?? error)}`);
    }
    return {};
  });

  on('command.run', {command: 'poc-clean'}, async ($) => {
    try {
      for (const key of await $.store.keys()) if (key.startsWith(KEY)) await $.store.delete(key);
      $.ui.log('poc-clean: done');
    } catch (error) {
      $.ui.log(`poc-clean failed: ${String(error?.message ?? error)}`);
    }
    return {};
  });
}
```

- [ ] **Step 5：驗證 plugin**

```bash
cd ~/Development/harness/handoff-poc && claude plugin validate . 2>&1 | tail -3
```

預期：`✔ Validation passed`（對 `tool.call` 這種 gating hook 沒有 `.catch` 的警告可以忽略，handoff-mod 也有同樣的警告）。失敗就照錯誤訊息修正後再跑。

---

### Task 2：跑 PoC（Tom 在 macOS 上操作）並記錄

這一步需要互動式 session，由 Tom 操作；執行者準備指令、讀結果、寫紀錄。PoC 用 `--plugin-dir` 載入，只在那次 session 有效。

**Files:**
- Modify: `docs/poc-results.md`（在檔尾加一節）

- [ ] **Step 0：暫時停用已安裝的 handoff-mod**

`~/.claude/settings.json` 啟用了 `handoff-mod@tomwangowa`（0.1.6，scope user）。不停用的話，PoC session 裡 0.1.6 也會載入：結束時在 `agent-skills` 留下自動筆記（`GEMINI.md` 是 untracked），PoC 4 的 `/clear` 也會跳出 0.1.6 的確認對話框。

```bash
claude plugin disable handoff-mod@tomwangowa
claude plugin list 2>&1 | grep -A3 "handoff-mod@tomwangowa"
```

預期：`Status:` 不是 `✔ enabled`。停用期間 Tom 新開的任何 session 都不會有 handoff-mod，Step 5 會重新啟用。

- [ ] **Step 1：PoC 1，store 並行寫入**

開兩個終端機，都在 `~/Development/harness/agent-skills`：

```bash
claude --plugin-dir ~/Development/harness/handoff-poc
```

在 A 輸入 `/poc-burst A`，一秒內在 B 輸入 `/poc-burst B`。兩邊都顯示 `wrote 300 keys` 後，**兩邊各自**輸入 `/poc-count`，記下兩個輸出。兩邊都 `/exit` 之後，直接數檔案裡的 key：

```bash
python3 -c 'import json,glob,os; d=json.load(open(glob.glob(os.path.expanduser("~/.claude/plugins/store/handoff-poc_inline-*.json"))[0])); print({t: sum(1 for k in d if k.startswith("poc:burst:"+t+":")) for t in "AB"})'
```

判定：

- **檔案**是 `{'A': 300, 'B': 300}`：並行寫入不會互相蓋掉，D22 的雙寫可以照計畫做。**不是**：停下來，回報 Tom，D22 要回到設計重新討論，不能繼續 Task 3 之後的步驟。
- **兩個 session 的 `/poc-count`** 都是 `{"A":300,"B":300}`：一個還開著的 session 看得到另一個 session 的寫入，spec 裡「新版放棄，舊版 session 重整清單 → 藏起來」成立。只看到自己的 300：照實記錄並回報 Tom，那一列的說法與 CHANGELOG 的「升級當下還開著的舊 session 看得到」要在 Task 13 改掉，但不擋實作。

做完 Step 2 到 Step 4 之前，先在其中一個 session 輸入 `/poc-clean`，避免 burst 的 key 混進後面的報告。

- [ ] **Step 2：PoC 3，快照是否早於第一個工具呼叫**

在 A 輸入一般的 prompt（不是 slash command）：`請建立檔案 poc-probe.txt，內容寫 hi`。送出後大約 8 秒內畫面應該沒有開始回應（hook 在等）。完成後輸入 `/poc-report`，記下 `poc:submit:<id>` 的 `doneAt` 與 `poc:tool:<id>` 的 `at`。

通過條件：`tool.at > submit.doneAt`。**不通過**：停下來，回報 Tom；快照要改到 `session.start`，需要先修改計畫的 Task 10 再繼續。

完成後刪掉測試檔：`rm ~/Development/harness/agent-skills/poc-probe.txt`。

- [ ] **Step 3：PoC 4，`/clear` 後 session id**

在 A 輸入 `/clear`，再輸入 `/poc-report`，看 `poc:ids` 裡 `/clear` 前後的 `id`。兩種結果都可以接受，照實記錄。

- [ ] **Step 4：PoC 2，結束時的成本**

在 A 輸入 `/exit`。在 `agent-skills` 開新 session（仍帶 `--plugin-dir`），輸入 `/poc-report`，記下 `poc:end:<上一個 id>` 的 `gitMs`、`statMs`、`entries`、`remainingMs`。再到一個 untracked 檔案比較多、日常有在用的 repo（例如 `工作 repo A`）重做一次（開 session、送一個 prompt、`/exit`、開新 session、`/poc-report`）。

通過條件：兩個 repo 都是 `gitMs + statMs` ≤ 250。250 到 500 之間：可以繼續，但要在紀錄裡註明。大於 500，或 `remainingMs` 小於 1000：停下來，回報 Tom，回頭修改 D23（降低上限或換做法）。

同一份報告裡也記下兩個 repo 的 `poc:submit:<id>` 的 `gitStatMs`，這是 0.2.0 在第一個 prompt 建立快照的成本。快照目前沒有自己的時限，只受 `git()` 的 5 秒逾時限制。任何一個 repo 的 `gitStatMs` 大於 500：回報 Tom，由他決定快照要不要加自己的時限（逾時就當成沒有快照），不擋 PoC 的其他判定。

- [ ] **Step 5：清掉 PoC 資料與 plugin，重新啟用 handoff-mod**

在任一個 PoC session 輸入 `/poc-clean`，全部 `/exit` 之後：

```bash
rm -rf ~/Development/harness/handoff-poc
claude plugin enable handoff-mod@tomwangowa
claude plugin list 2>&1 | grep -A3 "handoff-mod@tomwangowa"
```

預期：`Status: ✔ enabled`。另外確認 `agent-skills/.claude/handoffs/` 沒有 PoC 期間多出來的檔案，有的話跟 Tom 確認後刪除。

- [ ] **Step 6：寫進 `docs/poc-results.md`**

在檔尾加上這一節，數字換成實際量到的值，不要留空：

```markdown
## 0.2.0 實作前 PoC（2026-10-14，作者 macOS）

| # | 問題 | 結果 | 判定 |
| --- | --- | --- | --- |
| 1 | 兩個 session 同時寫同一個 store，資料會不會互相蓋掉；開著的 session 看不看得到另一個 session 的寫入 | 檔案：（實際輸出）；A 的 `/poc-count`：…；B 的 `/poc-count`：… | 通過／不通過；看得到／看不到 |
| 2 | 結束時 `git status -z --untracked-files=all` 加 50 個 `stat` 的耗時；第一個 prompt 建立快照的耗時 | agent-skills：gitMs=…、statMs=…、entries=…、remainingMs=…、submit gitStatMs=…；（第二個 repo 名稱）：… | 通過／註明／不通過 |
| 3 | `prompt.submit` hook 是否在第一個工具呼叫之前跑完 | submit.doneAt=…、tool.at=… | 通過／不通過 |
| 4 | `/clear` 後 session id 是否改變 | （改變／不變，附 id） | 記錄 |
```

- [ ] **Step 7：Commit**（先取得 Tom 同意）

```bash
git add docs/poc-results.md
git commit -m "docs(handoff-mod): record the 0.2.0 pre-implementation PoC"
```

---

### Task 3：`parseHandoff` 讓已處理的檔案帶 `meta`

**Files:**
- Modify: `hooks/handoff-file.js:44-75`
- Test: `tests/handoff-file.test.ts`

- [ ] **Step 1：寫失敗的測試**（加在 `tests/handoff-file.test.ts` 檔尾）

```ts
test('a closed file is not ok, but carries its meta so that it can close its copies (D20)', () => {
  const r: any = parseHandoff(handoffText({status: 'resumed'}));
  expect(r.ok).toBe(false);
  expect(r.reason).toBe('status');
  expect(r.meta.status).toBe('resumed');
  expect(r.meta.created).toBe(Date.parse('2026-10-06T18:30:00+08:00'));
  expect(r.fields.task).toBe('修正登入逾時');
});
test('a missing status, or a closed file with a bad created, carries no meta', () => {
  const missing: any = parseHandoff(handoffText({omit: ['status']}));
  expect(missing).toMatchObject({ok: false, reason: 'status'});
  expect(missing.meta).toBeUndefined();
  const badCreated: any = parseHandoff(handoffText({status: 'resumed', created: 'yesterday'}));
  expect(badCreated).toMatchObject({ok: false, reason: 'status'});
  expect(badCreated.meta).toBeUndefined();
  expect((parseHandoff(handoffText({created: 'yesterday'})) as any).reason).toBe('created');
});
```

- [ ] **Step 2：跑測試確認失敗**

```bash
claude plugin test . 2>&1 | grep -E "\(fail\)|Ran "
```

預期：`(fail) a closed file is not ok, but carries its meta ...`（`r.meta` 是 undefined）。

- [ ] **Step 3：實作**

把 `hooks/handoff-file.js` 的 `parseHandoff` 換成：

```js
/**
 * Parse a handoff file. Returns {ok:true, meta, fields} or {ok:false, reason}.
 * A closed file (a status that is set but not open) is {ok:false, reason:'status', meta, fields}: still not a handoff to
 * list, but its meta lets it close its copies in other working trees (D20).
 * Everything from the file is a plain string: nothing is executed, and branch/head are validated later, before git sees them.
 */
export function parseHandoff(input) {
  const parts = split(String(input ?? '').slice(0, MAX_READ));
  if (!parts) return {ok: false, reason: 'frontmatter'};
  const fm = {};
  for (const line of parts.front.split('\n')) {
    const m = /^([A-Za-z_][A-Za-z0-9_-]*):[ \t]*(.*)$/.exec(line);
    if (m && !(m[1] in fm)) fm[m[1]] = value(m[2]);
  }
  const open = OPEN_STATUSES.includes(fm.status);
  if (!open && (typeof fm.status !== 'string' || fm.status === '')) return {ok: false, reason: 'status'};
  const created = Date.parse(fm.created);
  if (!Number.isFinite(created)) return {ok: false, reason: open ? 'created' : 'status'};
  const text = (v) => (v === undefined || v === '' ? undefined : oneLine(v, 500));

  const sections = {};
  let current = null;
  for (const line of parts.body.split('\n')) {
    if (line.startsWith('## ')) {
      const heading = line.slice(3).trim();
      current = HEADINGS.find(([, pattern]) => pattern.test(heading))?.[0] ?? null;
      if (current && !sections[current]) sections[current] = [];
    } else if (current) sections[current].push(line);
  }
  const parsed = {
    meta: {
      schema: text(fm.schema), root: text(fm.root ?? fm.worktree), repo: text(fm.repo), branch: text(fm.branch),
      head: text(fm.head), created, status: fm.status, source: text(fm.source),
    },
    fields: {task: oneLine(fm.task ?? firstLine(sections.task) ?? '', 80), next: oneLine(firstLine(sections.next) ?? '', 120)},
  };
  return open ? {ok: true, ...parsed} : {ok: false, reason: 'status', ...parsed};
}
```

- [ ] **Step 4：跑測試確認通過**

```bash
claude plugin test . 2>&1 | tail -3
```

預期：`0 fail`。既有的 `files without a valid status or created are rejected` 仍通過（只檢查 `ok`）。

- [ ] **Step 5：Commit**（先取得 Tom 同意）

```bash
git add hooks/handoff-file.js tests/handoff-file.test.ts
git commit -m "feat(handoff-mod): keep the meta of a closed handoff file for merging copies (D20)"
```

---

### Task 4：`hooks/identity.js`

**Files:**
- Create: `hooks/identity.js`
- Test: `tests/identity.test.ts`

- [ ] **Step 1：寫失敗的測試**（新檔 `tests/identity.test.ts`）

```ts
import {test, expect} from 'claude-code/testing';
import {handoffKey, mergeCopies, stateKeys, claimKeys, newestState} from '../hooks/identity.js';

const DIR = '.claude/handoffs';
const ctx = {base: '/work/wt', repo: '/work/app', dir: DIR};
const copy = (path: string, o: {created?: string; closed?: boolean; task?: string} = {}) => ({
  path,
  meta: {created: Date.parse(o.created ?? '2026-10-09T03:15:22Z'), status: o.closed ? 'resumed' : 'in-progress'},
  fields: {task: o.task ?? 't', next: ''},
  closed: o.closed ?? false,
});

test('the key is the file name and the created time as ISO, however created was written', () => {
  expect(handoffKey('main--20261009-111522.md', Date.parse('2026-10-09T11:15:22+08:00'))).toBe('main--20261009-111522.md|2026-10-09T03:15:22.000Z');
  expect(handoffKey('a.md', Date.parse('2026-10-09T03:15:22Z'))).toBe(handoffKey('a.md', Date.parse('2026-10-09T11:15:22+08:00')));
});
test('copies of one file in several working trees become one item that knows every path, in scan order', () => {
  const items = mergeCopies([copy('/work/app/.claude/handoffs/a.md'), copy('/work/other/.claude/handoffs/a.md'), copy('/work/wt/.claude/handoffs/a.md')], ctx);
  expect(items.length).toBe(1);
  expect(items[0].key).toBe('a.md|2026-10-09T03:15:22.000Z');
  expect(items[0].paths).toEqual(['/work/app/.claude/handoffs/a.md', '/work/other/.claude/handoffs/a.md', '/work/wt/.claude/handoffs/a.md']);
});
test("the shown copy is this working tree's, then the main checkout's, then the first found", () => {
  expect(mergeCopies([copy('/work/app/.claude/handoffs/a.md'), copy('/work/wt/.claude/handoffs/a.md')], ctx)[0].path).toBe('/work/wt/.claude/handoffs/a.md');
  expect(mergeCopies([copy('/work/other/.claude/handoffs/a.md'), copy('/work/app/.claude/handoffs/a.md')], ctx)[0].path).toBe('/work/app/.claude/handoffs/a.md');
  expect(mergeCopies([copy('/x/.claude/handoffs/a.md'), copy('/y/.claude/handoffs/a.md')], ctx)[0].path).toBe('/x/.claude/handoffs/a.md');
});
test('a worktree nested under the base is not taken for the base', () => {
  const nested = '/work/wt/.claude/worktrees/n/.claude/handoffs/a.md';
  expect(mergeCopies([copy(nested), copy('/work/app/.claude/handoffs/a.md')], ctx)[0].path).toBe('/work/app/.claude/handoffs/a.md');
});
test('the shown copy gives the task and the meta', () => {
  const [item] = mergeCopies([copy('/work/app/.claude/handoffs/a.md', {task: 'main copy'}), copy('/work/wt/.claude/handoffs/a.md', {task: 'edited here'})], ctx);
  expect(item.fields.task).toBe('edited here');
});
test('another created time, or another name, stays a separate handoff', () => {
  const items = mergeCopies([copy('/x/.claude/handoffs/a.md'), copy('/y/.claude/handoffs/a.md', {created: '2026-10-09T03:15:23Z'}), copy('/y/.claude/handoffs/b.md')], ctx);
  expect(items.length).toBe(3);
});
test('one closed copy closes the item; with no closed copy it stays open', () => {
  expect(mergeCopies([copy('/x/.claude/handoffs/a.md'), copy('/y/.claude/handoffs/a.md', {closed: true})], ctx)[0].fileClosed).toBe(true);
  expect(mergeCopies([copy('/x/.claude/handoffs/a.md')], ctx)[0].fileClosed).toBe(false);
});
test("state and claim keys: the new key first, then every copy's old path key", () => {
  const [item] = mergeCopies([copy('/work/app/.claude/handoffs/a.md'), copy('/work/wt/.claude/handoffs/a.md')], ctx);
  expect(stateKeys(item)).toEqual(['state:id:a.md|2026-10-09T03:15:22.000Z', 'state:/work/app/.claude/handoffs/a.md', 'state:/work/wt/.claude/handoffs/a.md']);
  expect(claimKeys(item)).toEqual(['claim:id:a.md|2026-10-09T03:15:22.000Z', 'claim:/work/app/.claude/handoffs/a.md', 'claim:/work/wt/.claude/handoffs/a.md']);
});
test('newestState picks the latest record with a status and ignores the rest', () => {
  expect(newestState([undefined, {status: 'abandoned', at: 1}, {status: 'resumed', at: 5}, 'garbage', {at: 9}, null])).toEqual({status: 'resumed', at: 5});
  expect(newestState([undefined, null])).toBeUndefined();
});
```

- [ ] **Step 2：跑測試確認失敗**

```bash
claude plugin test . 2>&1 | grep -E "identity|Ran "
```

預期：`tests/identity.test.ts` 載入失敗（找不到 `../hooks/identity.js`）。

- [ ] **Step 3：實作 `hooks/identity.js`**

```js
/*
 * D20 to D22: one handoff is its file name plus its created time, so copies of one file in several working trees (or
 * left behind by a moved folder) are one handoff. State is kept under a key built from that, and, for 0.1.x, under each
 * copy's absolute path as well.
 */

const nameOf = (path) => path.slice(path.lastIndexOf('/') + 1);
const dirOf = (path) => path.slice(0, path.lastIndexOf('/'));

/** D20: `<file name>|<created as ISO>`; `created` is milliseconds, so two spellings of one instant give one key. */
export function handoffKey(name, created) {
  return `${name}|${new Date(created).toISOString()}`;
}

/**
 * Group `found` ({path, meta, fields, closed}) by key. Each item shows one copy: the one in `base`'s handoff folder,
 * else the one in `repo`'s, else the first found. `paths` keeps every copy in scan order; `fileClosed` is true when any
 * copy's own status is closed.
 */
export function mergeCopies(found, {base, repo, dir}) {
  const groups = new Map();
  for (const f of found) {
    const key = handoffKey(nameOf(f.path), f.meta.created);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(f);
  }
  const rank = (f) => (dirOf(f.path) === `${base}/${dir}` ? 0 : repo && dirOf(f.path) === `${repo}/${dir}` ? 1 : 2);
  return [...groups].map(([key, copies]) => {
    const shown = copies.reduce((best, f) => (rank(f) < rank(best) ? f : best));
    return {key, path: shown.path, paths: copies.map((f) => f.path), meta: shown.meta, fields: shown.fields, fileClosed: copies.some((f) => f.closed)};
  });
}

/** D21, D22: the new key first, then every copy's old `state:<path>`. New keys start with `id:`, old ones with `/`. */
export const stateKeys = (item) => [`state:id:${item.key}`, ...item.paths.map((path) => `state:${path}`)];

/** The same for claims. */
export const claimKeys = (item) => [`claim:id:${item.key}`, ...item.paths.map((path) => `claim:${path}`)];

/** The newest stored record that has a status, or undefined. Anything else in the store is ignored. */
export function newestState(records) {
  let best;
  for (const record of records) {
    if (!record || typeof record !== 'object' || typeof record.status !== 'string') continue;
    if (!best || Number(record.at) > Number(best.at)) best = record;
  }
  return best;
}
```

- [ ] **Step 4：跑測試確認通過**

```bash
claude plugin test . 2>&1 | tail -3
```

預期：`0 fail`。

- [ ] **Step 5：Commit**（先取得 Tom 同意）

```bash
git add hooks/identity.js tests/identity.test.ts
git commit -m "feat(handoff-mod): add handoff identity and copy merging (D20, D21)"
```

---

### Task 5：`hooks/snapshot.js`

**Files:**
- Create: `hooks/snapshot.js`
- Test: `tests/snapshot.test.ts`

- [ ] **Step 1：寫失敗的測試**（新檔 `tests/snapshot.test.ts`）

```ts
import {test, expect} from 'claude-code/testing';
import {parseStatusZ, takeBaseline, hasNewEntry, changedSince, BASELINE_MAX} from '../hooks/snapshot.js';

const before = takeBaseline([
  {code: ' M', path: 'a.ts', mtimeMs: 100},
  {code: '??', path: 'GEMINI.md', mtimeMs: 50},
  {code: ' D', path: 'gone.ts', mtimeMs: null},
], 3);
const same = () => [
  {code: ' M', path: 'a.ts', mtimeMs: 100},
  {code: '??', path: 'GEMINI.md', mtimeMs: 50},
  {code: ' D', path: 'gone.ts', mtimeMs: null},
];

test('-z output: plain entries, a rename that carries its old path, untracked and Chinese names, deletions', () => {
  expect(parseStatusZ(' M src/a.ts\0R  new.ts\0old.ts\0?? 筆記.md\0 D gone.ts\0')).toEqual([
    {code: ' M', path: 'src/a.ts'}, {code: 'R ', path: 'new.ts'}, {code: '??', path: '筆記.md'}, {code: ' D', path: 'gone.ts'},
  ]);
  expect(parseStatusZ('')).toEqual([]);
  expect(parseStatusZ(undefined as any)).toEqual([]);
});
test('a baseline keeps at most BASELINE_MAX entries and says when the status was longer', () => {
  const entries = Array.from({length: BASELINE_MAX}, (_, i) => ({code: '??', path: `f${i}`, mtimeMs: i}));
  expect(takeBaseline(entries, BASELINE_MAX)).toEqual({entries, truncated: false});
  expect(takeBaseline(entries, BASELINE_MAX + 1).truncated).toBe(true);
  expect(takeBaseline([...entries, {code: '??', path: 'extra', mtimeMs: 1}], BASELINE_MAX + 1).entries.length).toBe(BASELINE_MAX);
});
test('nothing touched, including a deletion from before: no change', () => {
  expect(changedSince(before, same())).toBe(false);
});
test('a file written again: change', () => {
  expect(changedSince(before, same().map((e) => (e.path === 'a.ts' ? {...e, mtimeMs: 101} : e)))).toBe(true);
});
test('a new file: change', () => {
  expect(changedSince(before, [...same(), {code: '??', path: 'new.ts', mtimeMs: 1}])).toBe(true);
});
test('staging only changes the code, and that is a change', () => {
  expect(changedSince(before, same().map((e) => (e.path === 'a.ts' ? {...e, code: 'M '} : e)))).toBe(true);
});
test('a file deleted during the session: change', () => {
  expect(changedSince(before, same().map((e) => (e.path === 'a.ts' ? {code: ' D', path: 'a.ts', mtimeMs: null} : e)))).toBe(true);
});
test('a file that cannot be read now, and is not a deletion: change', () => {
  expect(changedSince(before, same().map((e) => (e.path === 'a.ts' ? {...e, mtimeMs: null} : e)))).toBe(true);
});
test('a file that went back to clean is not a change', () => {
  expect(changedSince(before, same().filter((e) => e.path !== 'a.ts'))).toBe(false);
});
test('hasNewEntry looks at codes and paths only', () => {
  expect(hasNewEntry(before, [{code: ' M', path: 'a.ts'}])).toBe(false);
  expect(hasNewEntry(before, [{code: 'M ', path: 'a.ts'}])).toBe(true);
  expect(hasNewEntry(before, [{code: '??', path: 'other'}])).toBe(true);
});
```

- [ ] **Step 2：跑測試確認失敗**

```bash
claude plugin test . 2>&1 | grep -E "snapshot|Ran "
```

預期：`tests/snapshot.test.ts` 載入失敗（找不到 `../hooks/snapshot.js`）。

- [ ] **Step 3：實作 `hooks/snapshot.js`**

```js
/*
 * D23: an end-of-session note is written only when this session changed the working tree. The first request records
 * what was already dirty (code, path, mtime); the end compares against it.
 */

export const BASELINE_MAX = 50;

const isDeletion = (code) => code.includes('D');
const idOf = (entry) => `${entry.code}\u0000${entry.path}`;

/**
 * Parse `git status --porcelain -z`: NUL-separated `XY path` entries, paths relative to the repository root and never
 * quoted. A rename or copy is followed by its old path as one more field, which is skipped.
 */
export function parseStatusZ(stdout) {
  const fields = String(stdout ?? '').split('\0');
  const entries = [];
  for (let i = 0; i < fields.length; i++) {
    const field = fields[i];
    if (field.length < 4) continue;
    const code = field.slice(0, 2);
    entries.push({code, path: field.slice(3)});
    if (/[RC]/.test(code)) i++;
  }
  return entries;
}

/** `statted` are {code, path, mtimeMs} (a deletion has null); `total` is how many entries git listed. */
export function takeBaseline(statted, total) {
  return {
    entries: statted.slice(0, BASELINE_MAX).map(({code, path, mtimeMs}) => ({code, path, mtimeMs: mtimeMs ?? null})),
    truncated: total > BASELINE_MAX,
  };
}

/** Is any of `current` ({code, path}) missing from the baseline? Needs no stat. */
export function hasNewEntry(baseline, current) {
  const known = new Set(baseline.entries.map(idOf));
  return current.some((entry) => !known.has(idOf(entry)));
}

/**
 * Did the session change anything? Yes for a new code and path, a different mtime, or an unreadable file that is not a
 * deletion. A deletion from before the session that was left alone is null on both sides, which is no change.
 */
export function changedSince(baseline, current) {
  const before = new Map(baseline.entries.map((entry) => [idOf(entry), entry.mtimeMs]));
  for (const entry of current) {
    if (!before.has(idOf(entry))) return true;
    if (entry.mtimeMs === null && !isDeletion(entry.code)) return true;
    if (before.get(idOf(entry)) !== entry.mtimeMs) return true;
  }
  return false;
}
```

- [ ] **Step 4：跑測試確認通過**

```bash
claude plugin test . 2>&1 | tail -3
```

預期：`0 fail`。

- [ ] **Step 5：Commit**（先取得 Tom 同意）

```bash
git add hooks/snapshot.js tests/snapshot.test.ts
git commit -m "feat(handoff-mod): add the working-tree snapshot and comparison (D23)"
```

---

### Task 6：`tryClaim` 收一組 key

**Files:**
- Modify: `hooks/claim.js:16-30`
- Test: `tests/claim.test.ts`

- [ ] **Step 1：改既有測試的呼叫方式，並加新測試**

在 `tests/claim.test.ts` 把每個 `tryClaim({id: 'h1', ` 換成 `tryClaim({keys: ['claim:h1'], `（共 6 處，用全部取代）。然後在檔尾加：

```ts
test('with several keys, a live claim on any of them blocks, and nothing is written', async () => {
  const store = fakeStore({'claim:/old/path': {sessionId: 'B', at: now - 1000}});
  const r: any = await tryClaim({keys: ['claim:id:k', 'claim:/old/path'], sessionId: 'A', now, store});
  expect(r).toMatchObject({won: false, holder: 'B'});
  expect(store.data.get('claim:id:k')).toBeUndefined();
});
test('a free handoff with several keys is claimed under every key', async () => {
  const store = fakeStore();
  const keys = ['claim:id:k', 'claim:/a', 'claim:/b'];
  expect(((await tryClaim({keys, sessionId: 'A', now, store})) as any).won).toBe(true);
  for (const key of keys) expect(store.data.get(key)).toEqual({sessionId: 'A', at: now});
});
```

- [ ] **Step 2：跑測試確認失敗**

```bash
claude plugin test . 2>&1 | grep -E "\(fail\)|Ran "
```

預期：`claim.test.ts` 多個 `(fail)`（`tryClaim` 還在讀 `id`，寫成 `claim:undefined`）。

- [ ] **Step 3：實作**

把 `hooks/claim.js` 的 `tryClaim` 換成：

```js
/**
 * Claim a handoff for this session under every key in `keys` (the new key first, then each copy's old path key, D22).
 * A live claim by another session under any key wins. A get followed by a set is not atomic, so the first key is read
 * back and the winner is whoever is there. If the store fails, resuming is still allowed: `degraded` says the duplicate
 * guard is off.
 */
export async function tryClaim({keys, sessionId, now, store}) {
  try {
    for (const key of keys) {
      const view = claimView(await store.get(key), sessionId, now);
      if (view.state === 'other') return {won: false, holder: view.holder};
    }
    for (const key of keys) await store.set(key, {sessionId, at: now});
    const back = await store.get(keys[0]);
    return valid(back) && back.sessionId === sessionId ? {won: true} : {won: false, holder: valid(back) ? back.sessionId : undefined};
  } catch {
    return {won: true, degraded: true};
  }
}
```

- [ ] **Step 4：更新唯一的呼叫者，保持全綠**

`hooks/register.js` 的 `resume` 裡，把

```js
  const claim = await tryClaim({id: item.id, sessionId, now, store: {get: (key) => $.store.get(key), set: (key, value) => $.store.set(key, value)}});
```

換成（行為不變，仍是一個 key；Task 7 會換成完整的 key 清單）

```js
  const claim = await tryClaim({keys: [`claim:${item.id}`], sessionId, now, store: {get: (key) => $.store.get(key), set: (key, value) => $.store.set(key, value)}});
```

- [ ] **Step 5：跑測試確認通過**

```bash
claude plugin test . 2>&1 | grep -E "\(fail\)|Ran "; claude plugin test . 2>&1 | tail -3
```

預期：`0 fail`。

- [ ] **Step 6：Commit**（先取得 Tom 同意）

```bash
git add hooks/claim.js hooks/register.js tests/claim.test.ts
git commit -m "feat(handoff-mod): let a claim cover several store keys (D22)"
```

---

### Task 7：清單合併、狀態查詢與雙寫（D20 至 D22）

**Files:**
- Modify: `hooks/register.js`（import、`readHandoffs`、`buildList`、新增 `storeGetAll` 與 `writeState`、`resume`、`abandon`）
- Test: `tests/register.test.ts`（檔尾新增一節）

- [ ] **Step 1：寫失敗的測試**（加在 `tests/register.test.ts` 檔尾）

```ts
// --- 0.2.0: one handoff, many copies (D20 to D22) -------------------------------------------------------------------
const WT_DIR = '/work/wt/.claude/handoffs';
const wtCopyA = `${WT_DIR}/feat-login-timeout--20261006-183000.md`;
const KEY_A = 'feat-login-timeout--20261006-183000.md|2026-10-06T10:30:00.000Z';
const TWO_TREES = {'worktree list --porcelain': [0, 'worktree /work/app\nHEAD 781ac6b\nbranch refs/heads/feat/login-timeout\n\nworktree /work/wt\nHEAD 781ac6b\nbranch refs/heads/feat/wt\n\n'] as [number, string]};
const bothCopies = {[fileA]: handoffText(), [wtCopyA]: handoffText()};

test('copies of one handoff in two working trees are listed once, from this working tree (D20)', async ($, on) => {
  const w = world(on, {git: TWO_TREES, files: bothCopies});
  await startSession($);
  await w.flush();
  expect(w.lastStatus()).toBe('有 1 筆未完成交接，輸入 /handoff-resume 查看');
  await (await mountBand($)).press({key: 'resume-0'});
  expect(w.rec.fills[0]).toContain(fileA);
  expect(w.rec.fills[0]).not.toContain(wtCopyA);
});
test('a copy whose own file says resumed closes the other copies (D20)', async ($, on) => {
  const w = world(on, {git: TWO_TREES, files: {[fileA]: handoffText(), [wtCopyA]: handoffText({status: 'resumed'})}});
  await startSession($);
  await w.flush();
  expect(w.rec.statuses.filter((s) => s !== undefined).length).toBe(0);
});
test("a 0.1.x record under one copy's path still hides the handoff (D21)", async ($, on) => {
  const w = world(on, {git: TWO_TREES, files: bothCopies, store: {[`state:${wtCopyA}`]: {status: 'abandoned', at: NOW - 1000, sessionId: 'old'}}});
  await startSession($);
  await w.flush();
  expect(w.rec.statuses.filter((s) => s !== undefined).length).toBe(0);
});
test('drop writes the new key and the old key of every copy (D22)', async ($, on) => {
  const w = world(on, {git: TWO_TREES, files: bothCopies});
  await $.command.run({command: 'handoff-resume', args: 'drop 1'});
  for (const key of [`state:id:${KEY_A}`, `state:${fileA}`, `state:${wtCopyA}`]) expect(w.store.get(key)).toMatchObject({status: 'abandoned', sessionId: 'sess-A'});
});
test('resuming claims and records under the new key and every old key (D22)', async ($, on) => {
  const w = world(on, {git: TWO_TREES, files: bothCopies});
  await startSession($);
  await w.flush();
  await (await mountBand($)).press({key: 'resume-0'});
  for (const key of [`claim:id:${KEY_A}`, `claim:${fileA}`, `claim:${wtCopyA}`]) expect(w.store.get(key)).toMatchObject({sessionId: 'sess-A'});
  for (const key of [`state:id:${KEY_A}`, `state:${fileA}`, `state:${wtCopyA}`]) expect(w.store.get(key)).toMatchObject({status: 'resumed'});
});
test("a 0.1.x claim on one copy blocks resuming the handoff (D22)", async ($, on) => {
  const w = world(on, {git: TWO_TREES, files: bothCopies, store: {[`claim:${wtCopyA}`]: {sessionId: 'sess-B', at: NOW - 1000}}});
  await startSession($);
  await w.flush();
  const band = await mountBand($);
  expect(await band.find({key: 'resume-0'})).toBeUndefined();
  expect(await band.find({type: 'Text', text: '另一個 session 正在接續'})).toBeDefined();
});
```

- [ ] **Step 2：跑測試確認失敗**

```bash
claude plugin test . 2>&1 | grep -E "\(fail\)|Ran "
```

預期：新的 6 個測試裡至少 `listed once`、`drop writes the new key`、`resuming claims and records` 失敗。

- [ ] **Step 3：實作，import**

在 `hooks/register.js` 第 7 行 `import {tryClaim, claimView} from './claim.js';` 之後加：

```js
import {mergeCopies, stateKeys, claimKeys, newestState} from './identity.js';
```

- [ ] **Step 4：實作，`readHandoffs` 收已處理的副本**

把 `readHandoffs` 裡的

```js
          const parsed = parseHandoff(await $.fs.read(path));
          if (parsed.ok) found.push({path, meta: parsed.meta, fields: parsed.fields});
```

換成

```js
          const parsed = parseHandoff(await $.fs.read(path));
          if (parsed.ok) found.push({path, meta: parsed.meta, fields: parsed.fields, closed: false});
          // D20: a closed copy is kept so that it can close its copies in other working trees; it is never listed.
          else if (parsed.reason === 'status' && parsed.meta) found.push({path, meta: parsed.meta, fields: parsed.fields, closed: true});
```

- [ ] **Step 5：實作，`buildList`**

把 `storeGet` 之後到 `buildList` 結束（`/** Collect, rank and describe ...` 那整個函式）換成：

```js
/** Read `keys` one by one; a failed read is undefined. */
async function storeGetAll($, keys) {
  const values = [];
  for (const key of keys) values.push(await storeGet($, key));
  return values;
}

/** Collect, merge (D20), rank and describe the unfinished handoffs for this working tree and its repository. */
async function buildList($) {
  const lang = config.lang;
  const sessionId = await $.session.id();
  const now = await $.clock.now();
  const base = await projectBase($);
  const repo = await repoRoot($);
  const found = await readHandoffs($, await candidateDirs($, base, repo));
  const items = [];
  for (const group of mergeCopies(found, {base, repo, dir: DIR})) {
    // D21: the new key first, then each copy's old path key, so that records written by 0.1.x still count.
    const record = newestState(await storeGetAll($, stateKeys(group)));
    const claims = await storeGetAll($, claimKeys(group));
    items.push({
      ...group,
      effectiveStatus: record ? record.status : group.fileClosed ? 'closed' : group.meta.status,
      claimedByOther: claims.some((claim) => claimView(claim, sessionId, now).state === 'other'),
    });
  }
  const ranked = rankHandoffs(items, {base, repo, now});
  const picked = (await read($, expanded)) ? [...ranked.shown, ...ranked.rest] : ranked.shown;
  const views = [];
  for (const item of picked) {
    const facts = await freshnessFacts({meta: item.meta, git: (args) => git($, args)});
    views.push({
      id: item.key,
      path: item.path,
      stateKeys: stateKeys(item),
      claimKeys: claimKeys(item),
      title: t(lang, 'list.item', {n: views.length + 1, task: item.fields.task || item.path.split('/').pop(), branch: item.meta.branch ?? '-', age: age(lang, now - item.meta.created)}),
      next: item.fields.next ? t(lang, 'list.next', {next: item.fields.next}) : '',
      facts: facts.map((fact) => factText(lang, fact)),
      auto: item.meta.source === 'auto',
      older: Boolean(item.olderAuto),
      claimed: item.claimedByOther,
    });
  }
  return {items: views, total: ranked.shown.length + ranked.collapsed};
}
```

- [ ] **Step 6：實作，`writeState`、`resume`、`abandon`**

在 `/** Resume one handoff: ...` 之前加：

```js
/** D22: write the new key and every copy's old path key. The new key decides success; an old key that fails is only traced. */
async function writeState($, item, record) {
  const [first, ...old] = item.stateKeys;
  await $.store.set(first, record);
  for (const key of old) {
    try { await $.store.set(key, record); } catch (error) { trace($, `old state key not written: ${key}: ${String(error?.message ?? error)}`); }
  }
}
```

把 `resume` 裡的三行

```js
  const claim = await tryClaim({keys: [`claim:${item.id}`], sessionId, now, store: {get: (key) => $.store.get(key), set: (key, value) => $.store.set(key, value)}});
```
```js
  try { await $.store.set(`state:${item.id}`, {status: 'resumed', at: now, sessionId}); } catch { /* Resuming still works without the record. */ }
```
```js
  await $.prompt.fill({text: t(lang, 'resume.prompt', {path: item.id})});
```

分別換成

```js
  const claim = await tryClaim({keys: item.claimKeys, sessionId, now, store: {get: (key) => $.store.get(key), set: (key, value) => $.store.set(key, value)}});
```
```js
  try { await writeState($, item, {status: 'resumed', at: now, sessionId}); } catch { /* Resuming still works without the record. */ }
``````js
  await $.prompt.fill({text: t(lang, 'resume.prompt', {path: item.path})});
```

把 `abandon` 的本體換成：

```js
async function abandon($, item, now, sessionId) {
  try {
    await writeState($, item, {status: 'abandoned', at: now, sessionId});
    return true;
  } catch {
    return false;
  }
}
```

- [ ] **Step 7：跑測試確認通過**

```bash
claude plugin test . 2>&1 | grep -E "\(fail\)|Ran "; claude plugin test . 2>&1 | tail -3
```

預期：`0 fail`。既有的 `state:${fileA}`、`claim:${fileA}` 斷言照樣通過，因為舊 key 也有寫。

- [ ] **Step 8：Commit**（先取得 Tom 同意）

```bash
git add hooks/register.js tests/register.test.ts
git commit -m "feat(handoff-mod): list one handoff per identity and keep 0.1.x state readable (D20-D22)"
```

---

### Task 8：60% 提示不看 git 狀態（D24）

**Files:**
- Modify: `hooks/register.js`（`checkThreshold` 與它上方的註解）
- Test: `tests/register.test.ts`（改寫 3 個既有測試）

- [ ] **Step 1：改寫測試**

在 `tests/register.test.ts` 把下面三個測試整段

```ts
test('nothing is asked below the threshold, without a percentage, on a clean tree, or outside git', async ($, on) => {
  ...
});
test('a clean working tree is not unfinished work', async ($, on) => {
  ...
});
test('outside a git tree nothing is asked', async ($, on) => {
  ...
});
```

換成

```ts
test('nothing is asked below the threshold or without a percentage', async ($, on) => {
  const below = world(on, {git: DIRTY});
  await startSession($);
  await turnAt($, below, 59);
  await turnAt($, below, undefined);
  expect(below.lastStatus()).toBe(undefined);
});
test('a clean working tree is asked too, and git status is not run for it (D24)', async ($, on) => {
  const w = world(on, {git: {'status --porcelain': [0, '']}});
  await startSession($);
  await turnAt($, w, 80);
  expect(w.lastStatus()).toBe(STATUS(80));
  expect(await (await mountBand($)).find({key: 't1-agree'})).toBeDefined();
  expect(w.rec.git.some((call) => call.startsWith('status'))).toBe(false);
});
test('outside a git tree it is asked too (D24)', async ($, on) => {
  const w = world(on, {git: {'rev-parse --show-toplevel': [128, ''], 'worktree list --porcelain': [128, '']}, repo: null});
  await startSession($);
  await turnAt($, w, 80);
  expect(w.lastStatus()).toBe(STATUS(80));
});
```

- [ ] **Step 2：跑測試確認失敗**

```bash
claude plugin test . 2>&1 | grep -E "\(fail\)|Ran "
```

預期：`(fail) a clean working tree is asked too ...`、`(fail) outside a git tree it is asked too (D24)`。

- [ ] **Step 3：實作**

把 `checkThreshold` 上方的註解與函式換成：

```js
/**
 * T1: after a turn, ask once per threshold when the context is filling up (D1, design component 2). Since D24 the working
 * tree is not looked at: a clean tree and a folder outside git are asked too. No percentage still means do not ask.
 */
async function checkThreshold($) {
  const percent = (await $.session.usage())?.context?.percent;
  const state = await readT1($);
  const seen = onPercentSeen(state, percent);
  if (seen !== state) {
    // Compaction or /clear made the percentage fall: forget which thresholds were asked, and take any open prompt down.
    await update($, nextAt, () => seen.nextAt);
    await update($, askedAt, () => seen.askedAt);
    if ((await read($, t1Percent)) > 0) await closeT1($);
  }
  if (typeof percent !== 'number' || percent < effectiveThreshold(seen, config)) return;
  const decision = decideTrigger({
    percent, config, state: seen, idle: true,
    hasUnfinishedSign: true,
    handoffRunning: (await read($, handoffStartedAt)) > 0,
  });
  trace($, `threshold: percent=${percent} at=${decision.at} -> ${decision.action}`);
  if (decision.action !== 'ask') return;
  await update($, askedAt, () => decision.at);
  await update($, t1Percent, () => Math.max(1, percent));
  await syncStatus($);
}
```

- [ ] **Step 4：跑測試確認通過**

```bash
claude plugin test . 2>&1 | tail -3
```

預期：`0 fail`。

- [ ] **Step 5：Commit**（先取得 Tom 同意）

```bash
git add hooks/register.js tests/register.test.ts
git commit -m "feat(handoff-mod): ask at the context threshold whatever the working tree looks like (D24)"
```

---

### Task 9：`world.ts` 的 `gitDelays`

只延遲指定的 git 指令，Task 11 的子期限測試要用。

**Files:**
- Modify: `tests/world.ts:15`、`tests/world.ts:46-53`

- [ ] **Step 1：改 `world` 的參數型別**

在第 15 行的參數型別裡，`gitDelay?: number` 後面加 `; gitDelays?: Record<string, number>`。

- [ ] **Step 2：改 `process.run` 替身**

把

```ts
  on('process.run', async ($: any, e: any) => {
    if (e.argv[0] === 'chmod') { rec.chmods.push(e.argv.slice(1)); return {value: {exitCode: 0, stdout: '', stderr: ''}}; }
    if (o.gitDelay) await clock.sleep(o.gitDelay);
    const key = e.argv.slice(1).join(' ');
    rec.git.push(key);
```

換成

```ts
  on('process.run', async ($: any, e: any) => {
    if (e.argv[0] === 'chmod') { rec.chmods.push(e.argv.slice(1)); return {value: {exitCode: 0, stdout: '', stderr: ''}}; }
    const key = e.argv.slice(1).join(' ');
    // gitDelays slows one command only; gitDelay slows every git call.
    const delay = o.gitDelays?.[key] ?? o.gitDelay;
    if (delay) await clock.sleep(delay);
    rec.git.push(key);
```

- [ ] **Step 3：跑測試確認沒有破壞既有行為**

```bash
claude plugin test . 2>&1 | tail -3
```

預期：`0 fail`。

- [ ] **Step 4：Commit**（先取得 Tom 同意）

```bash
git add tests/world.ts
git commit -m "test(handoff-mod): let the test world slow down one git command"
```

---

### Task 10：第一個 request 記下快照（D23 前半）

**Files:**
- Modify: `hooks/register.js`（import、常數、`statEntries`、`takeSessionBaseline`、`recordRequest`）
- Test: `tests/register.test.ts`（slice f）

- [ ] **Step 1：寫失敗的測試**

在 `tests/register.test.ts` 的 slice f，`const talk = ...` 那個 helper 結束之後，加：

```ts
const STATUS_Z = 'status --porcelain -z --untracked-files=all';
const tree = (stdout: string): Record<string, [number, string]> => ({[STATUS_Z]: [0, stdout]});

test('the first request records what was already dirty, and later requests keep it (D23)', async ($, on) => {
  const w = world(on, {git: tree('?? GEMINI.md\0 D gone.ts\0'), files: {'/work/app/GEMINI.md': 'notes'}});
  await startSession($);
  await talk($, w);
  const first = w.store.get('last:sess-A').baseline;
  expect(first).toEqual({entries: [{code: '??', path: 'GEMINI.md', mtimeMs: NOW - 3600_000}, {code: ' D', path: 'gone.ts', mtimeMs: null}], truncated: false});
  w.files.set('/work/app/GEMINI.md', {text: 'edited', mtimeMs: NOW + 5});
  await talk($, w, 'second request', 'second answer');
  expect(w.store.get('last:sess-A').baseline).toEqual(first);
});
test('an unreadable dirty file leaves no baseline, and later requests do not take one (D23)', async ($, on) => {
  const w = world(on, {git: tree(' M missing.ts\0')});
  await startSession($);
  await talk($, w);
  expect(w.store.get('last:sess-A').baseline).toBe(null);
  w.files.set('/work/app/missing.ts', {text: 'here now', mtimeMs: NOW});
  await talk($, w, 'again', 'ok');
  expect(w.store.get('last:sess-A').baseline).toBe(null);
});
test('more than 50 dirty entries: the baseline is cut and says so (D23)', async ($, on) => {
  const names = Array.from({length: 51}, (_, i) => `f${i}.ts`);
  const w = world(on, {git: tree(names.map((n) => `?? ${n}\0`).join('')), files: Object.fromEntries(names.map((n) => [`/work/app/${n}`, 'x']))});
  await startSession($);
  await talk($, w);
  const baseline = w.store.get('last:sess-A').baseline;
  expect(baseline.truncated).toBe(true);
  expect(baseline.entries.length).toBe(50);
});
```

- [ ] **Step 2：跑測試確認失敗**

```bash
claude plugin test . 2>&1 | grep -E "\(fail\)|Ran "
```

預期：這 3 個 `(fail)`（`baseline` 是 undefined）。

- [ ] **Step 3：實作，import 與常數**

在 `import {mergeCopies, ...} from './identity.js';` 之後加：

```js
import {parseStatusZ, takeBaseline, hasNewEntry, changedSince, BASELINE_MAX} from './snapshot.js';
```

在 `const NOTE_DEADLINE_MS = 1500;` 之後加：

```js
// D23: -z keeps non-ASCII names unquoted so that they can be stat-ed; all untracked files, because a folder's mtime does
// not move when a file inside it changes.
const STATUS_ARGS = ['status', '--porcelain', '-z', '--untracked-files=all'];
const COMPARE_DEADLINE_MS = 500;
```

- [ ] **Step 4：實作，`statEntries`、`takeSessionBaseline`、`recordRequest`**

把 `recordRequest` 整個函式換成：

```js
/** stat each entry under `root`. A deletion is null without a stat; any other failure throws when `strict`, else is null. */
async function statEntries($, root, entries, {strict}) {
  const out = [];
  for (const entry of entries) {
    if (entry.code.includes('D')) {
      out.push({...entry, mtimeMs: null});
      continue;
    }
    try {
      out.push({...entry, mtimeMs: (await $.fs.stat(`${root}/${entry.path}`)).mtimeMs});
    } catch (error) {
      if (strict) throw error;
      out.push({...entry, mtimeMs: null});
    }
  }
  return out;
}

/** D23: what was already dirty before this session did anything, or null when that cannot be told (the old rule then applies). */
async function takeSessionBaseline($) {
  try {
    const status = await git($, STATUS_ARGS);
    if (status.exitCode !== 0) return null;
    const entries = parseStatusZ(status.stdout);
    return takeBaseline(await statEntries($, await projectBase($), entries.slice(0, BASELINE_MAX), {strict: true}), entries.length);
  } catch (error) {
    trace($, `baseline not taken: ${String(error?.message ?? error)}`);
    return null;
  }
}

/**
 * Keep the newest request, masked and cut, for the end-of-session note. One record per session; each prompt replaces it.
 * The first request also fixes the baseline (D23); later requests keep it, even when it is null, so that a baseline is
 * never taken after the session has started changing files.
 */
async function recordRequest($, text) {
  if (!config.autoNote || !text.trim() || (await $.session.surfaces()).length === 0) return;
  const key = `${LAST_PREFIX}${await $.session.id()}`;
  const previous = await storeGet($, key);
  const baseline = previous && typeof previous === 'object' && 'baseline' in previous ? previous.baseline : await takeSessionBaseline($);
  await $.store.set(key, {request: cleanForNote(text, QUOTE_MAX), response: '', at: await $.clock.now(), baseline});
}
```

- [ ] **Step 5：跑測試確認通過**

```bash
claude plugin test . 2>&1 | grep -E "\(fail\)|Ran "; claude plugin test . 2>&1 | tail -3
```

預期：`0 fail`。既有的 `the last request and answer are kept masked and cut, one record for the session` 仍通過（它用 `toMatchObject` 比對 request 與 response）。

- [ ] **Step 6：Commit**（先取得 Tom 同意）

```bash
git add hooks/register.js tests/register.test.ts
git commit -m "feat(handoff-mod): record what was dirty at the first request of a session (D23)"
```

---

### Task 11：結束時比對，只在有變化時寫筆記（D23 後半）

**Files:**
- Modify: `hooks/register.js`（新增 `sessionChanged`、改 `writeEndNote`、刪除 `dirtyPaths`）
- Test: `tests/register.test.ts`（slice f：改 6 個既有測試、加 7 個新測試）

- [ ] **Step 1：改既有的結束筆記測試**

在 slice f（`--- slice f: the end-of-session note`）裡：

1. `ending with unfinished work writes a facts-only note that the list can read back` 整段換成：

```ts
test('ending a session that changed a file writes a facts-only note that the list can read back', async ($, on) => {
  const w = world(on, {git: tree(' M src/login.ts\0'), files: {'/work/app/src/login.ts': 'old'}});
  await startSession($);
  await talk($, w, `fix it, password = ${SECRET}`, 'changed src/login.ts');
  w.files.set('/work/app/src/login.ts', {text: 'new', mtimeMs: NOW + 1});
  await $.session.end(END);
  const path = notePath(w);
  expect(path).toMatch(/\/work\/app\/\.claude\/handoffs\/feat-login-timeout--\d{8}-\d{6}--auto\.md$/);
  const text = w.files.get(path).text;
  expect(text).not.toContain(SECRET);
  expect(text).toContain('source: auto');
  expect(text).toContain('> fix it, password =');
  expect(text).toContain('src/login.ts');
  expect(parseHandoff(text).ok).toBe(true);
  expect(w.rec.chmods).toEqual([['600', path]]);
  expect(w.rec.writes.some(([p, body]) => p.endsWith('.git/info/exclude') && body.includes('.claude/handoffs/'))).toBe(true);
  expect(w.store.get('last:sess-A')).toBeUndefined();
});
```

2. `no note when the tree is clean, ...` 裡的 `world(on, {git: {'status --porcelain': [0, '']}})` 換成 `world(on, {git: tree('')})`。
3. `a /clear writes no note (T2 owns it) and drops the record`、`a session with no recorded request writes nothing`、`with HANDOFF_AUTO_NOTE=off ending the session writes nothing` 三個測試裡的 `git: DIRTY` 換成 `git: tree(' M src/login.ts\0')`。
4. `out of time means no file at all, and the record is still deleted` 裡的 `{git: DIRTY, gitDelay: 1000}` 換成 `{git: tree(' M src/login.ts\0'), gitDelay: 1000}`。

- [ ] **Step 2：加新測試**（接在 Task 10 加的三個測試後面）

```ts
test('a file that was dirty before the session and left alone writes no note (D23)', async ($, on) => {
  const w = world(on, {git: tree('?? GEMINI.md\0'), files: {'/work/app/GEMINI.md': 'notes'}});
  await startSession($);
  await talk($, w, 'what does handoff-mod do?', 'it hands work off');
  await $.session.end(END);
  expect(notePath(w)).toBeUndefined();
  expect(w.store.get('last:sess-A')).toBeUndefined();
});
test('a deletion from before the session, left alone, writes no note (D23)', async ($, on) => {
  const w = world(on, {git: tree(' D gone.ts\0')});
  await startSession($);
  await talk($, w);
  await $.session.end(END);
  expect(notePath(w)).toBeUndefined();
});
test('a new file written during the session writes a note, with its Chinese name intact (D23)', async ($, on) => {
  const git = tree('?? GEMINI.md\0');
  const w = world(on, {git, files: {'/work/app/GEMINI.md': 'notes'}});
  await startSession($);
  await talk($, w);
  git[STATUS_Z] = [0, '?? GEMINI.md\0?? 筆記.md\0'];
  w.files.set('/work/app/筆記.md', {text: 'new', mtimeMs: NOW + 1});
  await $.session.end(END);
  expect(w.files.get(notePath(w)).text).toContain('- 筆記.md');
});
test('staging a file during the session counts as a change (D23)', async ($, on) => {
  const git = tree(' M a.ts\0');
  const w = world(on, {git, files: {'/work/app/a.ts': 'x'}});
  await startSession($);
  await talk($, w);
  git[STATUS_Z] = [0, 'M  a.ts\0'];
  await $.session.end(END);
  expect(notePath(w)).toBeDefined();
});
test('without a baseline, as in a record from 0.1.x, a dirty tree writes as before (D23)', async ($, on) => {
  const w = world(on, {git: tree('?? GEMINI.md\0'), files: {'/work/app/GEMINI.md': 'notes'}});
  await startSession($);
  w.store.set('last:sess-A', {request: 'fix it', response: 'ok', at: NOW});
  await $.session.end(END);
  expect(notePath(w)).toBeDefined();
});
test('a cut baseline writes as before (D23)', async ($, on) => {
  const w = world(on, {git: tree('?? GEMINI.md\0'), files: {'/work/app/GEMINI.md': 'notes'}});
  await startSession($);
  w.store.set('last:sess-A', {request: 'fix it', response: 'ok', at: NOW, baseline: {entries: [], truncated: true}});
  await $.session.end(END);
  expect(notePath(w)).toBeDefined();
});
test('a comparison that misses its sub-deadline writes as before (D23)', async ($, on) => {
  const w = world(on, {git: tree('?? GEMINI.md\0'), gitDelays: {[STATUS_Z]: 700}, files: {'/work/app/GEMINI.md': 'notes'}});
  await startSession($);
  w.store.set('last:sess-A', {request: 'fix it', response: 'ok', at: NOW, baseline: {entries: [{code: '??', path: 'GEMINI.md', mtimeMs: NOW - 3600_000}], truncated: false}});
  const ending = $.session.end(END);
  await w.clock.advance(1000);
  await ending;
  expect(notePath(w)).toBeDefined();
});
```

最後一個測試的對照組是 `a file that was dirty before the session and left alone writes no note`：同樣的快照與工作樹，沒有延遲時不寫，所以寫出筆記只可能是子期限造成的。

- [ ] **Step 3：跑測試確認失敗**

```bash
claude plugin test . 2>&1 | grep -E "\(fail\)|Ran "
```

預期至少：`(fail) ending a session that changed a file writes ...`（`writeEndNote` 還在跑 `status --porcelain`，替身回 128，判成乾淨）、`(fail) a new file written during the session ...`、`(fail) staging a file ...`、`(fail) without a baseline ...`、`(fail) a cut baseline ...`、`(fail) a comparison that misses its sub-deadline ...`。

- [ ] **Step 4：實作，`sessionChanged`**

刪除 `const dirtyPaths = (porcelain) => ...` 那一行，在原處加：

```js
/**
 * D23: did this session change the working tree? With no usable baseline, or when git status and the stats miss the
 * sub-deadline, the answer is yes: the old rule (dirty means write) is kept rather than losing a note.
 * `statusRun` is the git status already started by the caller, so that the sub-deadline covers it too.
 */
async function sessionChanged($, baseline, statusRun, root, budget) {
  if (!baseline || typeof baseline !== 'object' || baseline.truncated || !Array.isArray(baseline.entries)) return true;
  const verdict = await withDeadline(async () => {
    const status = await statusRun;
    if (status.exitCode !== 0) return true;
    const current = parseStatusZ(status.stdout);
    if (current.length > BASELINE_MAX || hasNewEntry(baseline, current)) return true;
    return changedSince(baseline, await statEntries($, root, current, {strict: false}));
  }, Math.min(COMPARE_DEADLINE_MS, budget / 2), (ms, callback) => $.clock.after(ms, callback));
  if (!('value' in verdict)) trace($, `end note: comparison ${verdict.timedOut ? 'ran out of time' : 'failed'}, writing as before`);
  return 'value' in verdict ? verdict.value : true;
}
```

- [ ] **Step 5：實作，`writeEndNote`**

把 `writeEndNote` 上方的註解第一句改成 `D4, D23: at the end of an interactive session that changed the working tree, write the facts-only note ...`（其餘照舊），並把 `withDeadline(async () => {` 之後到 `const note = buildEndNote({` 之前的內容換成：

```js
      const base = await projectBase($);
      const statusRun = git($, STATUS_ARGS);
      const changed = await sessionChanged($, record.baseline, statusRun, base, budget);
      const status = await statusRun;
      const dirty = status.exitCode === 0 ? parseStatusZ(status.stdout).map((entry) => entry.path) : [];
      const write = shouldWriteNote({interactive: true, turns: 1, hasUnfinishedSign: hasUnfinishedSign({gitDirty: dirty.length > 0 && changed}), reason: e.reason, config});
      trace($, `end note: reason=${e.reason} dirty=${dirty.length} changed=${changed} write=${write}`);
      if (!write) return false;
      const branch = (await git($, ['branch', '--show-current'])).stdout.trim();
      const head = (await git($, ['rev-parse', '--short', 'HEAD'])).stdout.trim();
      let root = base;
      try { root = (await $.session.root()) || base; } catch { /* The git toplevel stands in. */ }
```

（原本在 `head` 之後的 `const base = await projectBase($);` 已經移到最前面，不要留兩份。）

- [ ] **Step 6：跑測試確認通過**

```bash
claude plugin test . 2>&1 | grep -E "\(fail\)|Ran "; claude plugin test . 2>&1 | tail -3
```

預期：`0 fail`。

- [ ] **Step 7：驗證 plugin**

```bash
claude plugin validate --strict . 2>&1 | tail -1
```

預期：`✔ Validation passed`。

- [ ] **Step 8：Commit**（先取得 Tom 同意）

```bash
git add hooks/register.js tests/register.test.ts
git commit -m "feat(handoff-mod): write the end-of-session note only when the session changed the tree (D23)"
```

---

### Task 12：變異檢查

照 `.claude/CLAUDE.md`：每項弄壞一處、確認有測試變紅、再還原。每一項都用 `git checkout -- <檔案>` 還原（前面的 Task 都已 commit）。

**Files:** 不留任何變更。

- [ ] **Step 1：逐項執行**

每一項：改動 → `claude plugin test . 2>&1 | grep -E "\(fail\)|Ran "` → 記下哪些測試變紅 → `git checkout -- <檔案>`。

| # | 檔案 | 弄壞的方式 | 預期變紅（至少） |
| --- | --- | --- | --- |
| 1 | `hooks/identity.js` | `handoffKey` 改成 `return \`${name}\|${created}\|${Math.random()}\`;` | `copies of one handoff in two working trees are listed once` |
| 2 | `hooks/register.js` | `buildList` 的 `stateKeys(group)` 改成 `stateKeys(group).slice(0, 1)` | `a 0.1.x record under one copy's path still hides the handoff` |
| 3 | `hooks/register.js` | `writeState` 刪掉 `for (const key of old)` 迴圈 | `drop writes the new key and the old key of every copy` |
| 4 | `hooks/claim.js` | 第一個迴圈改成只檢查 `keys[0]` | `a 0.1.x claim on one copy blocks resuming` |
| 5 | `hooks/register.js` | `checkThreshold` 的 `hasUnfinishedSign: true` 改成 `false` | `a clean working tree is asked too` |
| 6 | `hooks/register.js` | `recordRequest` 一律呼叫 `takeSessionBaseline($)` | `the first request records what was already dirty, and later requests keep it` |
| 7 | `hooks/register.js` | `sessionChanged` 最後一行改成 `return 'value' in verdict ? verdict.value : false;` | `a comparison that misses its sub-deadline writes as before` |
| 8 | `hooks/snapshot.js` | `changedSince` 刪掉 `&& !isDeletion(entry.code)` | `nothing touched, including a deletion from before`、`a deletion from before the session, left alone` |
| 9 | `hooks/snapshot.js` | `parseStatusZ` 刪掉 `if (/[RC]/.test(code)) i++;` | `-z output: plain entries, a rename ...` |
| 10 | `hooks/register.js` | `readHandoffs` 刪掉 `else if (parsed.reason === 'status' ...)` 那行 | `a copy whose own file says resumed closes the other copies` |

任何一項沒有測試變紅：停下來，補一個會變紅的測試，再重做那一項。

- [ ] **Step 2：確認全部還原**

```bash
git status --short . ; claude plugin test . 2>&1 | tail -3
```

預期：`git status` 沒有 `hooks/` 的變更；`0 fail`。

---

### Task 13：文件與版號

**Files:**
- Modify: `.claude-plugin/plugin.json`、`package.json`
- Modify: `README.md`、`README-en.md`
- Create: `CHANGELOG.md`
- Modify: `docs/superpowers/specs/2026-10-06-handoff-mod-design.md`
- Modify: `docs/implementation-results.md`

- [ ] **Step 1：版號**

`.claude-plugin/plugin.json` 與 `package.json` 的 `"version": "0.1.6"` 都改成 `"version": "0.2.0"`。

- [ ] **Step 2：`README.md`**

1. 「它做什麼」表格裡 60% 那一列換成：

```markdown
| context 用量到門檻（預設已用 60%） | 一個回合結束後，在輸入框上方問你要不要先交接：「同意」「再多 10% 再問」「這個 session 別再問」。不看工作樹乾不乾淨，非 git 目錄也會問。同時在輸入框下方放一行狀態。每個門檻只問一次。 |
```

2. 「session 結束」那一列換成：

```markdown
| session 結束（`/exit`、Ctrl-C 兩次、關分頁） | 若這個 session 改動了工作樹（新增、修改、刪除或 stage 了檔案），自動留下一份只含事實的筆記（最後一個要求、最後一段回應、branch、HEAD、有改動的檔案）。session 開始前就有、這次沒再動過的變更，不會觸發筆記。**含對話原文，見下方風險。** |
```

3. 表格下方那段的 `多個 worktree 會一起列出。` 換成 `多個 worktree 會一起列出；同一份交接（檔名與建立時間相同）在幾個 worktree 都有副本時，只列一筆。`
4. 「風險與界線」最後一條換成：

```markdown
- **用 git 狀態判斷這個 session 有沒有改動。** 第一次送出 prompt 時記下哪些檔案已經有變更、各自的修改時間，結束時比對。非 git 目錄不會自動留下筆記。有變更的檔案超過 50 個（untracked 資料夾裡的每個檔案都算）、或比對來不及在時限內做完時，照 0.1.x 的規則：有變更就留。
```

5. 「驗證狀態」表格的 `原生測試 153 項` 換成 Task 12 Step 2 實際印出的 pass 數。

- [ ] **Step 3：`README-en.md`**

1. Threshold row:

```markdown
| Context use reaches the threshold (default 60% used) | After a turn, a prompt above the input box asks whether to hand off first: "Agree", "Ask again at +10%", "Don't ask again this session". The working tree is not looked at; a folder outside git is asked too. A one-line status also appears under the input box. Each threshold is asked once. |
```

2. Session-end row:

```markdown
| The session ends (`/exit`, Ctrl-C twice, closing the tab) | If this session changed the working tree (added, modified, deleted or staged a file), it leaves a facts-only note (last request, last response, branch, HEAD, changed files). Changes that were there before the session and were left alone do not trigger a note. **This contains conversation text; see Risks below.** |
```

3. 第 20 行的 `Several worktrees are listed together.` 換成 `Several worktrees are listed together; copies of one handoff (same file name and created time) in several worktrees are listed once.`
4. Last risk bullet:

```markdown
- **Whether this session changed anything is judged by git state.** At the first prompt the mod records which files already have changes and their modification times, and compares at the end. A folder outside git gets no automatic note. With more than 50 changed files (every file inside an untracked folder counts), or when the comparison does not finish in time, the 0.1.x rule applies: any change means a note.
```

5. 驗證狀態表格的測試數改成同一個實際數字。

- [ ] **Step 4：新增 `CHANGELOG.md`**

```markdown
# Changelog

## 0.2.0（2026-10-14）

- 同一份交接複製到多個 worktree（或搬目錄留下副本）時，只列一筆。以前每個副本各算一筆。
- 放棄、接續的狀態不再只綁在檔案路徑上。從 0.1.x 升級，以前放棄、接續過的交接，只要檔案還在原位，狀態都保留。0.2.x 也會繼續寫 0.1.x 讀得懂的紀錄，所以升級當下還開著的舊 session、或降版，都看得到新版的放棄與接續。
- **行為改變：** 結束時的自動筆記只在這個 session 改動了工作樹時才寫。以前只要工作樹有任何未提交的變更（包括一個放著不管的 untracked 檔）就寫，每個 session 都會多一份。
- **行為改變：** context 用量到門檻時一律詢問，不再看工作樹乾不乾淨；非 git 目錄也會問。
- 自動筆記「有改動的檔案」裡的中文檔名，不再顯示成 git 的跳脫字串。

---

- Copies of one handoff in several worktrees (or left behind by a moved folder) are listed once. Each copy used to count separately.
- Abandoned and resumed states are no longer tied to the file path alone. After upgrading from 0.1.x, handoffs you abandoned or resumed keep that state as long as the file is where it was. 0.2.x also keeps writing records that 0.1.x reads, so an old session still open during the upgrade, or a downgrade, sees what the new version did.
- **Behavior change:** the end-of-session note is written only when this session changed the working tree. It used to be written whenever the tree had any uncommitted change (an untracked file left alone included), one more note per session.
- **Behavior change:** the context threshold prompt is shown whatever the working tree looks like, and outside git too.
- Non-ASCII file names in the note's changed-file list are no longer shown as git's escaped strings.
```

- [ ] **Step 5：設計主檔 `docs/superpowers/specs/2026-10-06-handoff-mod-design.md`**

1. 第 4 行的 `D19 補清單標頭的 drop 提示）` 換成 `D19 補清單標頭的 drop 提示；D20 至 D24 見 [交接的識別與「本 session 有變化」](2026-10-14-handoff-identity-and-session-change-design.md)）`。
2. 第 82 行（`**未完成跡象**` 那一段）結尾加上 `（2026-10-14 修訂：T1 依 D24 不再看這個條件；結束筆記依 D23 改成「這個 session 造成變化」。）`
3. D4 那一列的最後一格結尾加上 `；寫入條件 2026-10-14 改為 D23`。
4. 決定紀錄表 D19 那一列之後加：

```markdown
| D20 | 怎麼判斷兩個檔案是同一份交接 | **已決（Tom，2026-10-14）：** 檔名加 frontmatter 的 `created`（正規化成 ISO）；不改檔案格式。詳見 [交接的識別與「本 session 有變化」](2026-10-14-handoff-identity-and-session-change-design.md) |
| D21 | 0.1.x 以絕對路徑當 key 的 `state:` 紀錄怎麼辦 | **已決（Tom，2026-10-14）：** 讀取時先查新 key，查不到再用每個副本現在的路徑查舊 key；檔案已搬走的不處理 |
| D22 | 對已安裝的使用者相容到什麼程度 | **已決（Tom，2026-10-14）：** 雙向相容，接續、放棄、claim 都同時寫新 key 與每個副本的舊 key；0.2.x 全系列雙寫 |
| D23 | 結束筆記什麼時候寫 | **已決（Tom，2026-10-14）：** 這個 session 造成變化才寫；第一次 prompt 記快照，結束時比對；沒有快照、被截斷或比對逾時就照 D4 的舊規則 |
| D24 | 60% 提示看不看 git 狀態 | **已決（Tom，2026-10-14）：** 不看，到門檻就問；乾淨工作樹與非 git 目錄也問 |
```

- [ ] **Step 6：`docs/implementation-results.md`**

在檔尾加一節，數字照實填：

```markdown
## 0.2.0（D20 至 D24，2026-10-14）

| 項目 | 結果 |
| --- | --- |
| `claude plugin test .` | （Task 12 Step 2 的實際 pass 數）pass、0 fail；開工前 baseline 183 pass |
| `claude plugin validate --strict .` | （實際結果） |
| 變異檢查 | （Task 12 的 10 項，各自變紅的測試數） |
| 實作前 PoC | 見 [poc-results.md](poc-results.md) 的「0.2.0 實作前 PoC」 |
| 實機 | 見 Task 14 |
```

- [ ] **Step 7：找其他還寫著舊條件的地方**

```bash
grep -n -i "未提交\|uncommitted\|dirty\|乾淨\|clean tree\|working tree" .claude/CLAUDE.md skills/handoff/SKILL.md hooks/i18n.js
```

預期：沒有輸出（2026-10-14 寫計畫時查過）。有輸出的話，逐條判斷是否描述 T1 或結束筆記的觸發條件；是的話照 D23／D24 改寫，並把該檔加進 Step 8 的 `git add`。Task 2 若發現開著的 session 看不到另一個 session 的寫入，也在這一步把 `CHANGELOG.md` 中「升級當下還開著的舊 session……看得到」那句改成「重新開啟 session 後看得到」（中英文都改）。

- [ ] **Step 8：Commit**（先取得 Tom 同意）

```bash
git add .claude-plugin/plugin.json package.json README.md README-en.md CHANGELOG.md docs/superpowers/specs/2026-10-06-handoff-mod-design.md docs/implementation-results.md
git commit -m "docs(handoff-mod): document 0.2.0 and bump the version"
```

---

### Task 14：收尾驗證（含 Tom 的實機操作）

**Files:**
- Modify: `docs/implementation-results.md`（把實機結果補進 Task 13 加的那一節）

- [ ] **Step 1：自動驗證**

```bash
claude plugin test . 2>&1 | tail -3
claude plugin validate --strict . 2>&1 | tail -1
```

預期：`0 fail`；`✔ Validation passed`。

- [ ] **Step 2：實機劇本（Tom 在 macOS，`claude --plugin-dir ~/Development/harness/agent-skills/plugins/handoff-mod`）**

先照 Task 2 Step 0 停用已安裝的 0.1.6（`claude plugin disable handoff-mod@tomwangowa`，並用 `claude plugin list` 確認），否則 0.1.6 會跟著載入：第 1 項會留下 0.1.6 的自動筆記，第 3 項會看到 0.1.6 分開列出的副本，第 4 項分不出是哪個版本跳出提示。劇本做完後執行 `claude plugin enable handoff-mod@tomwangowa`，確認回到 `✔ enabled`。

再記下 `ls ~/Development/harness/agent-skills/.claude/handoffs/` 的內容。

| # | 操作 | 預期 |
| --- | --- | --- |
| 1 | 在 `agent-skills`（`GEMINI.md` 仍是 untracked）開 session，問一個不動檔案的問題，`/exit` | `.claude/handoffs/` 沒有新的 `--auto.md` |
| 2 | 開 session，請 Claude 建立 `scratch-handoff-test.txt`，`/exit` | 多一份 `--auto.md`，「有改動的檔案」列出 `scratch-handoff-test.txt`；之後刪掉這個檔案與那份筆記 |
| 3 | 把一份交接檔複製到另一個 worktree 的 `.claude/handoffs/`，開 session | 清單只列一筆；測完刪掉複本 |
| 4 | 在乾淨的 worktree 用 `HANDOFF_THRESHOLD_PCT=1 claude --plugin-dir ...` 開 session，送一個 prompt | 回合結束後出現交接提示 |
| 5 | 在有一份交接的 worktree 開 session，`/handoff-resume drop 1`，`/exit`；再執行 `python3 -c 'import json,glob,os; d=json.load(open(glob.glob(os.path.expanduser("~/.claude/plugins/store/handoff-mod_inline-*.json"))[0])); print([k for k,v in d.items() if k.startswith("state:") and isinstance(v,dict) and v.get("status")=="abandoned"])'` | 同一份交接同時有 `state:id:<檔名>\|<ISO>` 與 `state:<絕對路徑>` 兩個 key |

第 5 項不拿已安裝的 0.1.6 來比：`--plugin-dir` 用的是 inline store（`handoff-mod_inline-*.json`），已安裝的版本用 `handoff-mod_tomwangowa-*.json`，兩者本來就不共用，比不出雙寫有沒有作用。新舊版本共用同一個 store 時的行為，由 Task 7 的測試涵蓋。

- [ ] **Step 3：記錄實機結果**

把每一項的實際結果寫進 `docs/implementation-results.md` 0.2.0 那一節的「實機」一列（通過、不通過，附觀察到的現象）。不通過的項目要另外回報 Tom。

- [ ] **Step 4：Commit**（先取得 Tom 同意）

```bash
git add docs/implementation-results.md
git commit -m "docs(handoff-mod): record the 0.2.0 checks on macOS"
```

- [ ] **Step 5：交給 Tom 決定整合方式**

用 `superpowers:finishing-a-development-branch` 決定是否開 PR。合併到 `main` 後，0.2.0 要再合進 `production` 才會在 `~/.claude/skills` 生效；marketplace 讀的是預設分支。

---

## 自我檢查

**規格覆蓋：**

| 規格要求 | Task |
| --- | --- |
| D20 識別、合併、顯示路徑優先順序 | 4、7 |
| `parseHandoff` 已處理檔案帶 `meta`、寫入檢查不變 | 3（寫入檢查只看 `ok`，`findNewHandoff` 不用改） |
| D21 讀取時退回舊 key | 4（`stateKeys`）、7 |
| D22 雙寫 state 與 claim | 6、7 |
| D23 快照（`-z`、`--untracked-files=all`、刪除為 null、截斷、保留） | 5、10 |
| D23 結束比對、子期限涵蓋 git status、退回舊規則、中文檔名 | 5、11 |
| D24 門檻不看 git | 8 |
| 會刻意改寫的既有測試 4 個 | 8（2 個）、11（2 個，另外 4 個只換替身 key） |
| 實作前 PoC 4 項與判定門檻 | 1、2 |
| 版號、README、release note、設計主檔 | 13 |
| 變異檢查 | 12 |

**型別與名稱一致性：** `stateKeys`／`claimKeys` 在 Task 4 定義、Task 7 使用，清單項目的欄位名也是 `stateKeys`、`claimKeys`；`takeBaseline(statted, total)` 在 Task 5 定義、Task 10 用兩個參數呼叫；`statEntries($, root, entries, {strict})` 在 Task 10 定義、Task 11 以 `{strict: false}` 呼叫；`STATUS_Z` 與 `tree` 在 Task 10 定義於 slice f，Task 11 使用。

**已知風險：** PoC 3 實測不通過（hook 不會擋住回合），Tom 於 2026-10-14 選擇接受競態，Task 10 照原樣在第一個 prompt 建立快照，競態已列入 spec 的已知限制。實機上無法讓 0.1.6 與 0.2.0 共用同一個 store（`--plugin-dir` 用 inline store），所以「新舊版本同時運作」只有 Task 7 的測試涵蓋，實機只驗證雙寫確實寫出兩種 key。
