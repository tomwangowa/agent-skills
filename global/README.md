# `global/` — tracked mirrors of live global agent configs

> ⚠️ **這裡的檔案是全域指示的來源。** 切換完成後，`~/.claude/CLAUDE.md` 與 `~/.codex/AGENTS.md` 會是指向這裡的 symlink。改動請走 PR，合併並更新 production 後才生效。

| 檔案 | 生效位置（symlink 指向這裡） | 給誰用 |
|------|------------------------|--------|
| `CLAUDE.md` | `~/.claude/CLAUDE.md` | Claude Code 全域指示 |
| `AGENTS.md` | `~/.codex/AGENTS.md` | Codex 全域指示（含 superpowers 路由） |

## 為什麼要追蹤這份鏡像

把全域指示納入版本控管，方便 review 變更歷史、跨機器比對、與團隊分享路由規則。這裡的檔案是來源。切換完成後，`~/.claude/CLAUDE.md` 與 `~/.codex/AGENTS.md` 會是指向它們的 symlink，改這裡就等於改生效的設定。切換前，生效的仍是 `~/.claude` 與 `~/.codex` 下的實體檔案。

## 公開性

本 repo 是公開的，`global/` 的內容也會公開，這是刻意保留的設計。新增內容時，不要把個人路徑或識別資訊寫進鏡像。

## 修改流程

```sh
# 1. 在 worktree 裡改 global/CLAUDE.md 或 global/AGENTS.md，開 PR 合併到 main
# 2. 把 production 快轉到 main
# 3. 確認 production 裡的檔案與要切換的內容一致（cmp 通過）
# 4. 只在第 3 步通過後，才替換 ~/.claude/CLAUDE.md 與 ~/.codex/AGENTS.md 為 symlink
# 5. 替換後用 readlink 與 cmp 確認指向正確，再開新 session 生效
```

切換後，不要直接編輯 `~/.claude/CLAUDE.md` 或 `~/.codex/AGENTS.md`：它們是 symlink，寫進去的內容會落在 production worktree 裡，未提交，容易在下次快轉時出問題。

切換後若 production worktree 被移動、切分支或弄髒，symlink 會指向不存在或不一致的檔案，新 session 會讀不到全域指示，而且不會報錯。發現全域指示突然消失時，先檢查這兩個 symlink。

整合脈絡見 [`../docs/Superpowers-Integration.md`](../docs/Superpowers-Integration.md)。
