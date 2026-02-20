---
name: qa-to-notes
description: Save Claude Code Q&A conversations as structured Obsidian-compatible knowledge notes, or rewrite fact-checks into corporate-friendly Teams publish format. Use when user wants to persist conversation content as a markdown file, or rewrite analysis for team sharing.
---

# QA to Notes

Save Claude Code conversations as structured Obsidian-compatible knowledge notes. Supports three modes: **Standard** (reorganizes Q&A into encyclopedia-style articles with tables, Mermaid diagrams, and source links), **Direct write** (preserves source content verbatim without restructuring), and **Teams publish** (rewrites fact-checks into a corporate-friendly "extended analysis" format for group sharing — output only, no file write).

## Trigger

Use when the user says any of:
- 「幫我存下這段對話」「存成筆記」「save this conversation」
- 「把這段整理成筆記」「寫成 Obsidian 筆記」
- 「改寫成 Teams 版」「幫我寫發佈版」「publish」「寫成可以發的版本」
- Any intent to persist the current Q&A exchange as a markdown note
- Any intent to rewrite analysis for corporate group sharing

## Mode

This skill has three writing modes:

| Mode | Behavior | Output | Default? |
|------|----------|--------|----------|
| **Standard** | Restructure Q&A into encyclopedia-style knowledge article | Write to file | Yes |
| **Direct write** | Save source content verbatim — no restructuring, no rewriting | Write to file | No |
| **Teams publish** | Rewrite fact-check/analysis into corporate-friendly "extended analysis" format | Display in conversation only (no file write) | No |

### Mode detection

**Teams publish** triggers:
- 「改寫成 Teams 版」「幫我寫發佈版」「publish」「寫成可以發的版本」
- 「幫我改寫成可以分享的格式」「寫成群組版」
- Any intent to rewrite analysis for corporate/team group sharing

**Direct write** triggers:
- 「直接存」「原文存檔」「原封不動存下來」「不用整理」
- 「save as-is」「save raw」「verbatim」「把這篇直接存下來」
- Any explicit intent to preserve the original text without digestion

**Standard** triggers: everything else (default).

If ambiguous, ask:

> 要我**整理成知識筆記**、**原文直接存檔**、還是**改寫成 Teams 發佈版**？

## Workflow

### Step 1: Identify Scope

Determine what to save:
- **Default**: The entire Q&A exchange in the current conversation
- **If user specifies**: Only the portion they mention (e.g., "存下關於 Moltbook 的部分")
- **If appending**: User will reference an existing file — read it first, then append new content

Ask the user to confirm:
1. **Topic title** (for filename and H1 heading) — propose one based on the conversation
2. **Tags** — propose relevant tags based on content; user can override

### Step 2: Compose Note Body

**If Teams publish mode**: skip to [Step 2T](#step-2t-teams-publish).
**If direct write mode**: skip to [Step 2D](#step-2d-direct-write).
Otherwise continue below.

#### Step 2S: Restructure (Standard mode)

**Do NOT produce a verbatim conversation transcript.** Instead, reorganize the Q&A into a structured knowledge article:

- Extract all factual claims, explanations, and conclusions from the conversation
- Group related information under logical headings
- Resolve redundancies (if user asked the same thing twice, merge the answers)
- Preserve nuance and caveats — do not oversimplify
- Write in the same language the conversation was conducted in (typically Traditional Chinese)

**Structure template:**

```markdown
---
tags: [tag1, tag2, tag3]
date: YYYY-MM-DD
source: claude-code
---

# Topic Title

## 概述
[1-3 paragraph summary of the topic]

## [Section 1 — logical grouping]
[Content reorganized from Q&A]

## [Section 2]
[Content]

## [Section N]
[Content]

> [!tip] Key Insight
> [1-2 sentence distillation of the single most important takeaway from this topic]

## Actionable Follow-up
- [ ] [Concrete next step the user could take based on what was learned]
- [ ] [Another action item, if applicable]

## 引用來源
- [Source Title 1](URL1)
- [Source Title 2](URL2)
```

**Key Insight** and **Actionable Follow-up** are conditional sections:

| Section | Include when | Skip when |
|---------|-------------|-----------|
| Key Insight | The conversation produced a non-obvious conclusion, a corrected misconception, or a decisive judgment (e.g., "this tool is not worth using because X") | The topic is purely descriptive with no evaluative conclusion |
| Actionable Follow-up | There are concrete steps the user could take: install something, read a specific doc, make a decision, test a hypothesis | The topic is purely informational with no implied action |

- **Key Insight** uses Obsidian's `> [!tip]` callout syntax for visual prominence
- **Actionable Follow-up** uses checkbox format (`- [ ]`) so items are trackable in Obsidian

#### Step 2D: Direct Write {#step-2d-direct-write}

Preserve the source content **verbatim**. Do not restructure, reword, summarize, or merge.

1. Identify the target content — the conversation segment, article, fact-check report, or drafted text the user wants to save
2. Wrap it in the standard note structure (frontmatter + H1 title) but **do not alter the body**
3. If the source already contains headings, keep them as-is (do not renumber or restyle)
4. If the source contains `## 引用來源` or equivalent, keep it in place — do not duplicate in a separate section

**Direct write template:**

```markdown
---
tags: [tag1, tag2]
date: YYYY-MM-DD
source: claude-code
---

# Topic Title

[source content verbatim — no restructuring]
```

After composing the body, skip Step 3 and proceed to Step 4.

#### Step 2T: Teams Publish {#step-2t-teams-publish}

Rewrite the current conversation's fact-check / analysis into a corporate-friendly "extended analysis" format suitable for sharing in a company Teams group. **Output is displayed in conversation only — no file is written.**

After composing the body, **skip all remaining steps** (no frontmatter, no file path, no file write). Just display the result and stop.

##### Input

Identify the fact-check report and/or short commentary ("短評") from the current conversation. If multiple exist, ask the user which one to convert. If no fact-check or analysis is found in the current conversation, inform the user and suggest running `/narrative-auditor` first.

##### Transformation Rules

Apply these rules **in order**:

**1. Structure Rewrite**

| Original element | Teams version |
|-----------------|---------------|
| `🦤 Dodo Fact-Check` or `🦤 Dodo: ... fact-check ...` | `📌 延伸分析：[主題名稱]` |
| Opening line | `感謝 @_____ 分享...！我做了一些延伸研究，整理了幾個值得注意的脈絡。` |
| `## 關鍵發現` with CRITICAL/HIGH/MEDIUM/LOW sections | Reorganize into `### [N] 個值得關注的面向` — numbered, no severity labels |
| `## 省略分析` | Fold into `### 另一面也值得知道` — bulleted list, neutral tone |
| `## Steelman` | Integrate key points into the body naturally; do not keep as standalone section |
| `## 整體評估` | Distill into 1 paragraph woven into the narrative or the closing analogy |
| `## 引用來源` | Remove entirely (replaced by "私訊我" link at bottom) |

**2. Content Filtering**

Remove or transform these elements:

| Filter | Action |
|--------|--------|
| Owner's personal name | Remove all occurrences |
| `TrendLife` brand name | Replace with neutral terms: 「我們」「消費者安全領域」「我們在消費者端的定位」 |
| `🦤 Dodo` persona markers | Remove all occurrences |
| Verdict labels (`ACCURATE`, `MISLEADING`, `FALSE`, `OMITTED`, etc.) | Remove — rewrite as prose |
| Confidence tags (`[verified]`, `[corroborated]`, etc.) | Remove entirely |
| Severity labels (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`) | Remove entirely |
| Sharp metaphors that could feel confrontational in a corporate setting | Soften or replace with accessible analogies |

**3. Tone Calibration**

- Negative findings → frame as「另一面也值得知道」rather than judgments
- Replace confrontational phrases (「房間裡的大象」「稻草人」) with accessible analogies
- Use「值得注意」「有趣的是」instead of「問題在於」「被省略了」
- When referencing the original sharer's article, frame as「在這個基礎上延伸」not「這篇有問題」

**4. 論點 Section (Always Include)**

Every Teams publish output MUST end with a `### 💡 論點：[論點問句]` section.

Content sources (in priority order):
1. The `🏢 TrendLife 視角` section from the original fact-check (de-branded)
2. The `整體評估` section's strategic implications
3. The `短評`'s concluding insight
4. **Fallback**: If none of the above exist, write a general open-ended reflection connecting the topic to the team's consumer-facing domain

Writing style for the 論點 section:
- **Use concrete scenario examples** — e.g., 「想像你半夜三點跟 AI 聊...」 instead of abstract statements
- **Use contrast pairs** — e.g., 「偵測率高 2%」vs「掃描結果不會被賣」 to make points instantly clear
- **Conversational tone** — write as if explaining to a smart colleague over coffee, not presenting to a board
- **Bridge to team relevance** — connect insights to 「我們在消費者端的產品定位和溝通策略」 without naming specific brands or products

**5. Fixed Footer**

Every Teams publish output ends with:

```
📎 對「完整的分析（包含引用來源）」有興趣的同事可以私訊我。

（本分析使用 AI 工具輔助資料蒐集與初步整理，策略觀點為個人見解）
```

##### Output Template

```
📌 延伸分析：[主題名稱]

感謝 @_____ 分享...！我做了一些延伸研究，整理了幾個值得注意的脈絡。

---

### 背景
[2-3 句交代事件]

### [N] 個值得關注的面向
**1. [面向標題]**
[內容 — 事實 + 洞見，無 verdict 標籤]

**2. [面向標題]**
[內容]

...

### 另一面也值得知道
- [平衡觀點 1]
- [平衡觀點 2]
- [平衡觀點 3]

### [選填：一個類比]
[如果原始分析中有好的類比框架，保留並潤飾]

### 💡 論點：[論點問句]

[論點內容 — 具體場景舉例、對比句式、口語化、橋接到團隊相關性]

📎 對「完整的分析（包含引用來源）」有興趣的同事可以私訊我。

（本分析使用 AI 工具輔助資料蒐集與初步整理，策略觀點為個人見解）
```

##### What Teams Publish Does NOT Do

- Does not write files (display only — user copies manually to Teams)
- Does not guess the original sharer's name (always uses `@_____` placeholder)
- Does not include source URLs (directs to "私訊我" instead)
- Does not handle images or attachments

### Step 3: Add Visual Elements When They Clarify Structure

**Standard mode only.** Skip this step in direct write mode.

**Tables**: Use standard markdown tables for comparisons, feature lists, timelines, or structured data.

**Mermaid diagrams**: Use ONLY basic Mermaid syntax compatible with Obsidian's built-in renderer. Wrap in ` ```mermaid ` code blocks.

Supported diagram types (safe for Obsidian):
- `graph TD` / `graph LR` — flowcharts
- `sequenceDiagram` — sequence diagrams
- `gantt` — Gantt charts
- `classDiagram` — class diagrams
- `stateDiagram-v2` — state diagrams

**Avoid** newer Mermaid features that Obsidian may not support:
- `mindmap`
- `timeline`
- `quadrantChart`
- `sankey`
- `xychart`
- `block-beta`

Only add diagrams when they genuinely clarify relationships or flows. Do not force diagrams for content that can be expressed in 1-2 sentences or a flat list.

### Step 4: Generate Frontmatter

Required YAML frontmatter fields:

| Field | Value | Notes |
|-------|-------|-------|
| `tags` | Array of relevant tags | Propose based on content; user can override |
| `date` | `YYYY-MM-DD` | Date of the conversation |
| `source` | `claude-code` | Fixed value |

The user may request additional frontmatter fields — include them if asked.

### Step 5: Determine File Path and Name

**Default output directory** (configurable per user):
```
$QA_NOTES_DIR or the current working directory if unset
```

> **Setup**: Set the environment variable `QA_NOTES_DIR` to your Obsidian vault path, or the skill will use the current working directory. If the user specifies a path at invocation time, use that instead.

**Filename convention:** `TopicName_YYYY-MM-DD.md`
- Date matches the conversation date
- TopicName: concise, may use Chinese or English, no spaces (use hyphens)
- Example: `Moltbook是什麼_2026-02-16.md`

**If user specifies a different path**, use that instead.

### Step 6: Write or Append

**New file**: Use the Write tool to create the file.

**Append to existing file** (for follow-up questions):
1. Read the existing file first
2. Add a horizontal rule (`---`) separator
3. Add a new section with the date and new content:

```markdown
---

## [New Section Title] (YYYY-MM-DD)

[New content restructured from follow-up Q&A]
```

4. If new sources were referenced, **also append them** to the existing `## 引用來源` section (do not duplicate existing sources)
5. If new tags are relevant, add them to the frontmatter `tags` array

After writing, confirm to the user:
- File path written
- Brief summary of what was captured

## Example Output

```markdown
---
tags: [AI, agent, social-network, OpenClaw]
date: 2026-02-16
source: claude-code
---

# Moltbook 是什麼

## 概述

Moltbook 是一個 AI agent 專屬的社交網路，由 Matt Schlicht 於 2026 年 1 月推出。
平台模仿 Reddit 介面，只有經過驗證的 OpenClaw AI agent 能發文、留言、投票，
人類使用者只能旁觀。目前有超過 250 萬註冊 AI agent。

## 運作機制

1. 使用者將 markdown 安裝指令連結傳給 OpenClaw agent
2. Agent 自動執行安裝
3. 透過 heartbeat 機制每 4 小時自動上線互動
4. Agent 之間自主交流技術知識與自動化技巧

## 實際應用案例

| 案例 | 說明 |
|------|------|
| ADB over Tailscale | Agent 分享遠端控制 Android 手機的方法 |
| Webcam 擷取 | 使用 streamlink + ffmpeg 的技術筆記 |
| 議價買車 | Agent 自主完成購車議價流程 |

## 安全疑慮

Simon Willison 指出的風險：
- **Prompt injection**：heartbeat 機制是持續的攻擊面
- **致命三合一**：網路存取 + 金融操作 + 個人資料
- **Normalization of Deviance**：風險逐步升級無人在意

## 評價

MIT Technology Review 稱之為「peak AI theater」——表演性大於實用性。
對已有成熟工作流的開發者而言，實際生產力價值接近零。

> [!tip] Key Insight
> Moltbook 的真正意義不在實用性，而在於它是第一個大規模 AI agent 自主社交的實驗場。安全風險（heartbeat prompt injection、致命三合一）遠大於其對個人生產力的幫助。

## Actionable Follow-up
- [ ] 不需要安裝 Moltbook——現有 Claude Code 工作流已涵蓋其聲稱的生產力場景
- [ ] 持續關注 OpenClaw 的 gVisor 沙箱進展，作為 AI agent 安全的參考指標

## 引用來源

- [Simon Willison - Moltbook is the most interesting place on the internet](https://simonwillison.net/2026/Jan/30/moltbook/)
- [MIT Technology Review - Moltbook was peak AI theater](https://www.technologyreview.com/2026/02/06/1132448/moltbook-was-peak-ai-theater/)
```

## Example: Append to Existing Note

User previously saved a note about Moltbook. In a later session, they ask about OpenClaw security and then say "幫我把這段追加到 Moltbook 那篇筆記".

1. Read the existing `2026-02-16-Moltbook是什麼.md`
2. Add `---` separator after the last section (before `## 引用來源`)
3. Add new section:

```markdown
---

## OpenClaw 安全風險 (2026-02-17)

Fortune 和 CrowdStrike 均在 Steinberger 加入 OpenAI 前發文警告 OpenClaw 的安全風險...
```

4. Append new sources to existing `## 引用來源`
5. Add new tags (`security`, `OpenClaw`) to frontmatter

## Error Handling

1. **Output directory does not exist**: Warn the user and ask for a valid path. Do not create directories without user confirmation.
2. **File already exists (new note mode)**: Ask the user whether to overwrite, append, or choose a different filename.
3. **File not found (append mode)**: List markdown files in the output directory and ask the user to pick the correct one.
4. **Conversation too short**: If the Q&A has fewer than 2 exchanges, warn the user that there may not be enough content for a structured note — offer to save as-is or wait for more content.
5. **No sources in conversation**: If no URLs were referenced, omit the `## 引用來源` section entirely rather than leaving it empty.
6. **YAML frontmatter conflict (append mode)**: If existing frontmatter has conflicting values, preserve the original and note the conflict in a comment.
7. **Write failure**: If the Write tool fails (permissions, disk space), report the error and suggest the user check the path.

## Constraints

- **Never transcript (Standard mode)**: Always restructure. The output is a knowledge note, not a chat log. This constraint does not apply in direct write mode, where verbatim preservation is the entire point.
- **Language**: Match the conversation language. If the Q&A was in Traditional Chinese, the note is in Traditional Chinese. Code comments and technical terms may stay in English.
- **Mermaid safety**: Only use diagram types listed in Step 3. When in doubt, use a table instead.
- **No fabrication**: Only include information that was actually discussed in the conversation. Do not add external knowledge that wasn't part of the Q&A.
- **Source integrity**: Preserve all URLs exactly as they appeared. Do not shorten, redirect, or modify source links.
- **Frontmatter validity**: Ensure YAML frontmatter is syntactically valid. Escape special characters in tag values if needed.
- **File safety**: Before writing, verify the output directory exists. Before appending, read the existing file first. Never overwrite without reading.

## Security Considerations

- **Path validation**: Only write to paths within the user's Obsidian vault or explicitly specified directories. Reject paths containing `../` traversal.
- **No sensitive data**: If the conversation contains API keys, passwords, or credentials, strip them from the output and warn the user.
- **Content sanitization**: Sanitize any user-provided filenames to prevent path injection. Replace characters unsafe for filenames (`/`, `\`, `:`, `*`, `?`, `"`, `<`, `>`, `|`) with hyphens.
