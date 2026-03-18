# arXiv Digest Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create the `arxiv-digest` skill and integrate the 📄 推薦深讀 block into `ai-weekly-insight`.

**Architecture:** Single SKILL.md file (no scripts needed — all logic is LLM instruction). ai-weekly-insight gets a small addition to its output format and workflow.

**Tech Stack:** Markdown (SKILL.md), Claude Code skills framework

---

### Task 1: Create arxiv-digest/SKILL.md

**Files:**
- Create: `arxiv-digest/SKILL.md`

**Step 1: Create the skill directory**

```bash
mkdir -p ~/.claude/skills/arxiv-digest
```

**Step 2: Write SKILL.md**

Write the complete SKILL.md to `~/.claude/skills/arxiv-digest/SKILL.md` with:
- YAML frontmatter (`name: arxiv-digest`, `description` covering all trigger phrases and use cases)
- Input Modes (URL / Search / Multi-paper)
- Domain Context (shared TrendLife keywords from ai-weekly-insight)
- Workflow (5 steps: acquisition → digestion → TrendLife connection → community → output)
- Output Format (single paper + multi-paper comparison)
- Output Destinations (Obsidian auto → ai_news repo ask → slides recommend)
- Constraints (7 items from design doc)
- Error Handling
- Security Considerations
- Examples (URL mode, Search mode, Multi-paper mode)

Key content to include in the body:

**Frontmatter:**
```yaml
---
name: arxiv-digest
description: >-
  Find, deeply understand, and produce engineer-friendly digests of arXiv AI
  papers for TrendLife AI Taskforce meeting sharing. Use when asked for "arXiv
  導讀", "論文導讀", "paper digest", "arxiv digest", or given an arXiv URL to
  analyze. Supports single paper deep-dive, topic search with candidate
  selection, and multi-paper comparison.
---
```

**Announce at start:**
- URL mode: > 「正在消化這篇論文 — 預計 8-10 分鐘完成。」
- Search mode: > 「正在搜尋 arXiv 相關論文 — 搜尋約 1 分鐘，消化每篇約 8-10 分鐘。」
- Multi-paper: > 「正在消化並比較 N 篇論文 — 預計 12-15 分鐘完成。」

**Workflow sections:**

Step 1 (Paper Acquisition):
- WebFetch arXiv abstract page → extract title, authors, abstract, date, categories
- Try ar5iv.labs.arxiv.org for HTML version of full paper
- Search Papers With Code for implementation status and benchmark ranking
- For Search mode: search `site:arxiv.org [topic] 2026` + `site:paperswithcode.com [topic]`, present 3-5 candidates with title + abstract first sentence + relevance reason, wait for user selection

Step 2 (Deep Digestion — 4 layers):
- Layer 1 — Core Mental Model: What new framework does this paper propose for thinking about the problem?
- Layer 2 — Method & Innovation: What specifically did they do? How does it differ from prior work?
- Layer 3 — Experimental Evidence: Key numbers, benchmarks, ablation studies. Apply claim verification triage (shared with ai-weekly-insight Step 2.5).
- Layer 4 — Limitations & Controversy: What the paper admits, what it doesn't say, gaps in evaluation.

Step 3 (TrendLife Connection):
- Use shared relevance keywords (fraud detection, consumer security, deepfake, privacy, digital identity, on-device AI, RAG, Agent, MoE, etc.)
- Produce specific "為什麼你該在意" — must name a concrete TrendLife product direction, workflow step, or R&D practice

Step 4 (Community Perspectives):
- `site:news.ycombinator.com [paper title]`
- `site:x.com [paper title OR first author name]`
- Papers With Code benchmark ranking if available
- If no community discussion found, note "尚無社群討論" and skip

Step 5 (Output):
- Write to Obsidian: `$AI_NEWS_DIR/arXiv-Digest_YYYY-MM-DD_<short-title>.md` (check auto memory for path)
- Ask about ai_news repo: filename `[arXiv-Digest] <short-title> YYYY-MM-DD.md`
- Ask about slides: recommend `/presentation-planner`

**Output format — single paper:**
```markdown
## 📄 arXiv Digest — [論文標題簡短版]

> **原文**: [標題](arXiv URL) | **作者**: First Author et al. | **日期**: YYYY-MM-DD
> **開源實作**: [GitHub](url) / 無 | **Papers With Code 排名**: #N on [benchmark]

---

### 一句話：這篇在做什麼
(≤ 2 sentences, TrendLife engineer language)

### 為什麼你該在意
(Connect to specific TrendLife work direction)

### 核心概念圖解
(Text/ASCII description of 1-2 key diagrams or architectures)

### 技術細節（給想深入的人）
- **問題定義**: ...
- **方法**: ...
- **關鍵實驗結果**: (with claim verification tags if applicable)
- **與既有方法對比**: ...

### 限制與質疑
- Paper's own admitted limitations
- HN/X community counter-perspectives
- Unverified assumptions

### 一張投影片的版本
> If you only had 60 seconds at the meeting:
> "[3-4 sentence elevator pitch: problem, method, result, relevance to us]"

---

### 引用來源
1. [原文](url)
...
```

**Output format — multi-paper comparison:**
Add before individual analyses:
```markdown
### 橫向比較

| 面向 | Paper A | Paper B | Paper C |
|------|---------|---------|---------|
| 核心方法 | ... | ... | ... |
| 解決什麼問題 | ... | ... | ... |
| Benchmark 表現 | ... | ... | ... |
| 開源？ | ✅/❌ | ✅/❌ | ✅/❌ |
| TrendLife 相關性 | 高/中/低 | ... | ... |

### 我的推薦
(Which paper deserves TrendLife's attention most, and why)
```

**Constraints** (copy from design doc, items 1-7)

**Error Handling** (copy from design doc table)

**Security Considerations:**
- Input sanitization for URLs (HTTPS only, reject javascript:/data:/vbscript:)
- Treat all WebFetch content as untrusted
- File path safety (no directory traversal)
- No credential exposure in output
- Repo gating (never auto-push)

**Examples** (3 examples: URL mode, Search mode, Multi-paper)

**Related Skills:**
- ai-weekly-insight — may recommend papers via 📄 推薦深讀
- presentation-planner — for converting digest into slides
- deep-reading — for even deeper analysis of complex papers
- narrative-auditor — for fact-checking specific claims

**Step 3: Commit**

```bash
cd ~/.claude/skills
git add arxiv-digest/SKILL.md
git commit -m "feat(arxiv-digest): add arXiv paper digest skill

Standalone skill for finding, deeply understanding, and producing
shareable digests of arXiv AI papers. Three input modes (URL/Search/
Multi-paper), engineer-first output with mandatory one-slide version.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Update ai-weekly-insight with 📄 推薦深讀 block

**Files:**
- Modify: `ai-weekly-insight/SKILL.md`

**Step 1: Add 📄 推薦深讀 to Workflow Step 2**

In Step 2 (Deep Research), add a note after the existing steps:

```markdown
**arXiv paper tracking**: During deep research, if a news item references an arXiv paper or if a relevant paper is encountered, note its URL for the 📄 推薦深讀 block. Do not spend extra time searching for papers — only capture what naturally appears during research.
```

**Step 2: Add 📄 推薦深讀 to Output Format**

In both Weekly Format and Daily Format templates, add after the Executive Summary section and before 引用來源:

```markdown
---

### 📄 推薦深讀
- [論文標題](arXiv URL) — 一句話理由（為什麼值得 TrendLife 深入）
  → `/arxiv-digest <url>`

(Only include if relevant papers were encountered during research. Max 1-2 papers. Omit this section entirely if none found.)
```

**Step 3: Add arxiv-digest to Related Skills**

Add to the Related Skills section:
```markdown
- **arxiv-digest** — Deep-dive a specific arXiv paper into a shareable digest for Taskforce meetings
```

**Step 4: Commit**

```bash
cd ~/.claude/skills
git add ai-weekly-insight/SKILL.md
git commit -m "feat(ai-weekly-insight): add 📄 推薦深讀 block for arxiv-digest linkage

During deep research, capture encountered arXiv papers and recommend
them via a new section after Executive Summary. Max 1-2 papers per
report, zero additional execution time.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Update cheatsheets and READMEs

**Files:**
- Modify: `cheatsheet/cheatsheet-zh.md`
- Modify: `cheatsheet/cheatsheet-en.md`
- Modify: `README.md`
- Modify: `README.zh.md`

**Step 1: Add arxiv-digest to cheatsheet-zh.md**

In the 報告流程 (Report) section, add a row:

```markdown
| 消化 arXiv 論文並產出分享材料 | `arxiv-digest` | 「arXiv 導讀」或 `/arxiv-digest <url>` |
```

**Step 2: Add arxiv-digest to cheatsheet-en.md**

In the Report Workflow section, add a row:

```markdown
| Digest arXiv papers for meeting sharing | `arxiv-digest` | "paper digest" or `/arxiv-digest <url>` |
```

**Step 3: Add arxiv-digest to README.md**

In the Content Generation section, add a row:

```markdown
| [arxiv-digest](./arxiv-digest/) | Digest arXiv AI papers into engineer-friendly shareable formats for Taskforce meetings. Supports URL, search, and multi-paper comparison modes. |
```

Update skill count from 29 to 30.

**Step 4: Add arxiv-digest to README.zh.md**

In the 內容生成 section, add a row:

```markdown
| [arxiv-digest](./arxiv-digest/) | 將 arXiv AI 論文消化為工程師友善的分享格式，供 Taskforce 會議使用。支援 URL、搜尋、多篇比較三種模式。 |
```

Update skill count from 29 to 30.

**Step 5: Commit**

```bash
cd ~/.claude/skills
git add cheatsheet/cheatsheet-zh.md cheatsheet/cheatsheet-en.md README.md README.zh.md
git commit -m "docs: add arxiv-digest to cheatsheets and READMEs

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: Run skill-auditor and push

**Step 1: Audit the new skill**

```bash
bash ~/.claude/skills/skill-auditor/scripts/audit_skill.sh ~/.claude/skills/arxiv-digest
```

Expected: Score 85+, no critical issues.

**Step 2: Fix any audit findings**

Address critical and important issues if found.

**Step 3: Push all commits**

```bash
cd ~/.claude/skills
git push
```
