# Design: ai-weekly-insight Skill

**Date**: 2026-03-01
**Status**: Approved
**Author**: Tom (via Claude Code brainstorming)

## Problem

TrendLife AI Taskforce needs a weekly AI news analysis that goes beyond surface-level summaries. The existing auto-generated `AI 新聞摘要` (Gemini Flash API) provides only bullet-point summaries without business context or competitive analysis. Engineers need actionable insights tied to TrendLife's strategic direction.

## Solution

A monolithic Claude Code skill that automates the full pipeline: news search → three-dimension analysis → dual output (Obsidian + Confluence).

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Architecture | Monolithic Skill | Single user, stable workflow, proven by prototype |
| Input mode | Auto (default), with URL override | Auto handles 90% of cases; override for curated curation |
| Analysis depth | Full 3-dimension for all 5 | Prototype showed acceptable time (~5 min) |
| Obsidian output | Automatic | No review needed for local files |
| Confluence output | Manual confirm | Avoid accidental publishing to shared wiki |
| Skill integration | Independent | Keeps execution fast; fact-check via narrative-auditor on demand |
| TrendLife context | Static embed | 5 wiki pages confirmed stable by user |

## Workflow

1. **News Collection** (~1 min): 3 broad WebSearches → 10-15 candidates → relevance scoring → Top 5 (category-balanced)
2. **Deep Research** (~2 min): Per-news narrow + deep search, optional WebFetch
3. **Three-Dimension Analysis** (~2 min): Tech breakthrough / Business impact / Competitive dynamics
4. **Executive Summary**: Trend sentence + 4-tier recommendations (immediate/short/mid/ongoing)
5. **Output**: Obsidian auto-write → Confluence preview + confirm

## Output Destinations

- **Obsidian**: `[AI News dir]/AI-Weekly-Tech-Insight_YYYY-MM-DD.md`
- **Confluence**: `TrendLifeRD > AI News` (parentId: 2082834686), title: `AI Weekly Tech Insight - YYYY-MM-DD`

## Relationship to Existing Skills

- `narrative-auditor`: Complementary (fact-check individual news on demand)
- `qa-to-notes`: Complementary (Teams publish version on demand)
- `critical-research`: Complementary (deep-dive specific topics on demand)

## Prototype Validation

Ran 2026-03-01. Results:
- 3 rounds of WebSearch worked well for news collection
- 5 × 3-dimension analysis produced actionable content
- Total execution: ~5 minutes
- Output successfully published to both Obsidian and Confluence
