# arXiv Digest — Design Document

**Date**: 2026-03-18
**Status**: Approved
**Author**: Tom + Claude

## Problem

TrendLife AI Taskforce engineers need to stay current with AI research papers, but arXiv publishes ~500 AI papers/day. Reading and digesting papers for meeting sharing is time-consuming. No existing skill covers the full pipeline: find → understand → produce shareable material.

## Solution

A standalone skill `arxiv-digest` that finds, deeply understands, and produces engineer-friendly digests of arXiv papers for Taskforce meeting sharing.

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Standalone vs ai-weekly-insight mode | **Standalone** | Different workflow (depth vs breadth), different time budget, different output format |
| Deep-reading integration | **Borrow methodology, don't chain** | Avoid skill-to-skill call complexity; copy the 4-layer extraction model |
| Slides generation | **Recommend presentation-planner** | Don't reinvent; include "一張投影片版本" as minimum viable output |
| ai-weekly-insight linkage | **📄 推薦深讀 block** | Decoupled — ai-weekly-insight recommends, user manually triggers arxiv-digest |
| Confluence vs repo | **ai_news repo** | Consistent with daily insight destination |

## Input Modes

| Mode | Trigger | Behavior |
|------|---------|---------|
| **URL** | `/arxiv-digest <arXiv-url>` | Directly digest the paper |
| **Search** | `/arxiv-digest <topic/keywords>` | Search arXiv, present 3-5 candidates, user picks 1-2, then digest |
| **Multi-paper** | `/arxiv-digest <url1> <url2>` or "compare X and Y" | Side-by-side comparison + per-paper analysis |

## Workflow

1. **Paper acquisition**: Fetch abstract, metadata, ar5iv HTML, Papers With Code page
2. **Deep digestion** (4 layers): core mental model → method & innovation → experimental evidence → limitations & controversy
3. **TrendLife connection**: Score with shared relevance keywords, produce specific "為什麼你該在意"
4. **Community perspectives**: HN (`site:news.ycombinator.com`) + X (`site:x.com`) + Papers With Code ranking
5. **Output**: Obsidian (auto) → ai_news repo (ask) → Slides (recommend presentation-planner)

## Output Format

### Single Paper

```
📄 arXiv Digest — [Title]
├── 一句話：這篇在做什麼
├── 為什麼你該在意（TrendLife specific）
├── 核心概念圖解（text/ASCII, no-original-needed）
├── 技術細節（problem → method → results → comparison）
├── 限制與質疑（paper's own + HN/X community）
├── 一張投影片的版本（60-second elevator pitch）
└── 引用來源
```

### Multi-Paper Comparison

Same as single, plus a leading comparison table and "我的推薦" section.

## Output Destinations

| Destination | Behavior |
|-------------|----------|
| Obsidian (auto) | `$AI_NEWS_DIR/arXiv-Digest_YYYY-MM-DD_<short-title>.md` |
| ai_news repo (ask) | `[arXiv-Digest] <short-title> YYYY-MM-DD.md` |
| Slides (ask) | Recommend `/presentation-planner` |

## ai-weekly-insight Integration

Add `📄 推薦深讀` block after Executive Summary:
- Max 1-2 papers per report
- Only papers matching TrendLife relevance keywords
- Zero additional execution time (papers noted during existing research)
- Format: `[Title](url) — one-line reason → /arxiv-digest <url>`

## Constraints

1. Engineer-first perspective: "what engineering problem does this solve"
2. No fluff (shared with ai-weekly-insight)
3. Citations required
4. Claim verification (shared Step 2.5 triage)
5. Honest about limits: mark "需讀原文 Section X 確認" when uncertain
6. Time control: single ≤ 10 min, multi ≤ 15 min
7. "一張投影片版本" is mandatory

## Time Budget

| Mode | Target |
|------|--------|
| Single paper | ≤ 10 minutes |
| Multi-paper (2-3) | ≤ 15 minutes |
| Search mode (search + digest) | Search ~1 min + digest time |
