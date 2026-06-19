# `global/` — tracked mirrors of live global agent configs

> ⚠️ **這些是鏡像檔，不是真正的設定來源。** 編輯時請先改「源頭」，再重新鏡像回來，否則下次同步會把這裡的修改蓋掉。

| 檔案 | 源頭（真正生效的設定） | 給誰用 |
|------|------------------------|--------|
| `CLAUDE.md` | `~/.claude/CLAUDE.md` | Claude Code 全域指示 |
| `AGENTS.md` | `~/.codex/AGENTS.md` | Codex 全域指示（含 superpowers 路由） |

## 為什麼要追蹤這份鏡像

把全域指示納入版本控管，方便 review 變更歷史、跨機器比對、與團隊分享路由規則。但生效的永遠是 `~/.claude` / `~/.codex` 下的本尊。

## 修改流程（避免漂移）

```sh
# 1. 改源頭
$EDITOR ~/.codex/AGENTS.md        # 或 ~/.claude/CLAUDE.md
# 2. 重新鏡像回 repo
cp ~/.codex/AGENTS.md   global/AGENTS.md
cp ~/.claude/CLAUDE.md  global/CLAUDE.md
```

整合脈絡見 [`../docs/Superpowers-Integration.md`](../docs/Superpowers-Integration.md)。
