---
name: newsletter-digest
description: |
  Digest and categorize newsletter emails (.eml files) from a folder into a structured, topic-grouped summary.
  Use when user asks to organize newsletters, digest emails, summarize subscriptions,
  or mentions .eml files, newsletter folder, or email digest.
---

# Newsletter Digest

Read all `.eml` files from a specified folder, extract content, group by topic, and produce a structured digest for quick reading.

## Process

### Step 1: Parse .eml Files

Run the bundled parser script to extract structured data from all .eml files:

```bash
python3 ~/.claude/skills/newsletter-digest/scripts/parse_emls.py "<folder_path>" -o /tmp/newsletter-digest.json
```

- If the folder has subfolders, ask user whether to include them (add `--recursive` flag)
- The script handles: MIME parsing, HTML→text, encoding, signature/footer stripping
- Output: JSON with sender, subject, date, cleaned body for each email
- Read the resulting JSON file to proceed to classification

### Step 2: Classify by Topic

Analyze all emails and cluster them into topic groups. Typical categories include (but adapt based on actual content):

- AI 產業動態（模型發布、產業趨勢、企業策略）
- 產品管理（PM 方法論、指標、使用者研究）
- 工程與技術（架構、開發文化、工具）
- 商業與市場（市場分析、商業模式、融資）
- 科學與研究（學術論文、新技術突破）
- 生活與社會（非科技類內容）

Merge emails with similar or overlapping topics into the same group. A single email may appear in multiple groups if it covers multiple topics.

### Step 3: Generate Digest

For each topic group, output:

```markdown
## [主題名稱]（N 篇）

> 來源：[Source A]、[Source B]、...

### 重點摘要

[2-5 句話總結這個主題下所有文章的核心內容。不是逐篇摘要，
而是把相關文章的資訊合成一段連貫的敘述。]

### 各篇速覽

| 標題 | 來源 | 日期 | 一句話重點 |
|------|------|------|----------|
| [Article title] | [Source] | [Date] | [One sentence] |

### 💡 值得深讀

[如果某篇文章特別值得完整閱讀，在這裡標注並說明為什麼。
如果沒有特別突出的，省略這個區塊。]
```

### Step 4: Output Summary Header

At the top of the digest, add:

```markdown
# Newsletter Digest — [日期範圍]

**期間**：[最早日期] ~ [最新日期]
**信件數**：[N] 封
**主題數**：[N] 個
**閱讀時間**：約 [N] 分鐘

---
```

## Output Format

- Language: match the majority language of the emails. If mixed, use Traditional Chinese for the framework, preserve original titles in their original language.
- One markdown file containing all topic groups, ordered by number of articles (most articles first).
- At the end, add a section listing any emails that didn't fit into any topic group.

## Rules

- Do NOT invent information not in the original emails
- Preserve original article titles exactly as they appear
- If an .eml file cannot be parsed, note it in the output and continue
- If the folder contains non-.eml files, ignore them silently
- Strip email signatures, disclaimers, and unsubscribe footers from the analysis
- For HTML-heavy newsletters, extract the article text; ignore layout/styling/ads
