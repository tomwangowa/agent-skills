---
name: claude-workflow-designer
description: Use this skill when the user is designing a Claude Code workflow, choosing between mechanisms (hook/skill/subagent/MCP/CLAUDE.md), or packaging automation for team distribution. Also triggered by the /sos slash command.
disable-model-invocation: true
---

# Claude Code Workflow Designer

A guided framework for helping users pick the right Claude Code mechanism for their task — and warning them when they don't need one at all.

## Core principles

Read these before suggesting anything. They override individual mechanism preferences.

1. **One-shot tasks need no mechanism.** If the user will do this once and never again, just do the task. Suggesting a skill for a one-shot task wastes their time and yours.
2. **Mechanisms compose, they don't compete.** The right answer is often "skill + hook + MCP", not "pick one of these five".
3. **Start with the lowest setup cost.** Order from cheapest to most expensive: direct conversation → CLAUDE.md → user skill → auto skill → MCP → subagent → hook → plugin. When two mechanisms could work, pick the one further left.
4. **Always ask "will this repeat?" before "what mechanism?"** Frequency determines whether automation pays back its setup cost.
5. **Resist over-engineering.** If the user describes one task, design for one task. Don't volunteer a five-mechanism architecture when they asked how to format a file.
6. **Motive before specification.** Understand *why* the user wants this before designing *what* to build. Misdiagnosed motives produce over-engineered solutions.

## Mechanism heuristics

### Direct conversation (no mechanism)

**Use when:** the task is one-shot, exploratory, or the user is still figuring out what they want. Examples: "explain this error", "review this SQL", "what does this regex do".

**Don't use when:** the user has said "every time" or "I keep having to" — that's a repetition signal.

**Setup cost:** zero.

### CLAUDE.md

**Use when:** there are 3–10 cross-cutting rules that apply to *every* task in a repo or globally. Examples: "always use Traditional Chinese (Taiwan)", "prefer pytest over unittest", "this codebase uses tabs not spaces".

**Don't use when:** the rules are situational ("when writing SQL, do X" — that's an auto skill), or when there are more than ~10 rules (CLAUDE.md becomes noise that dilutes the important rules).

**Setup cost:** very low. Just edit a markdown file.

### Skill (auto-invoked)

**Use when:** Claude should automatically apply domain knowledge or conventions when a *situation* arises, without the user having to ask. Triggered by Claude reading the skill description and deciding it's relevant. Examples: "when writing Databricks SQL, follow our naming conventions", "when handling JIRA tickets in CPDT project, apply our triage rules".

**Don't use when:** the trigger is a specific user command (use a user skill instead), or when the knowledge is so universal it belongs in CLAUDE.md.

**Setup cost:** low–medium. Requires writing a clear `description` field that Claude can match against.

**Critical: write descriptions as symptoms, not categories.** The `description` field is the entire trigger mechanism. Use the sentence pattern "when the user [does X] / [is in situation Y]", not abstract task labels. Good: "when the user is writing TypeScript or Python in this repo". Bad: "Python coding standards enforcement". Symptom-shaped descriptions match against real user behaviour; category labels don't.

**When the content is large (≥30 rules, ≥10 pages, or a full document):** use the **reference file pattern**. Keep `SKILL.md` short — just the trigger description, the 3–5 most important rules, and a pointer like "for the full ruleset, read `references/full-style-guide.md`". Claude only loads references when it needs the detail. This is called *progressive disclosure* and it's how all mature Anthropic skills handle large knowledge bases. Stuffing 80 pages into `SKILL.md` makes Claude slower, less accurate, and harder to maintain.

### Skill (user-invoked, slash command)

**Use when:** the user wants to explicitly invoke a fixed workflow with a short command, optionally passing arguments. Examples: `/review-pr 1234`, `/deploy staging`, `/triage-case PROJ-5678`.

**Don't use when:** the workflow should run automatically based on context (use auto skill), or when it's a one-shot task.

**Setup cost:** low–medium. Same as auto skill, plus deciding on a memorable command name.

**Note:** user skills replaced the older "slash commands" feature. They use `$ARGUMENTS` to receive parameters.

### MCP server

**Use when:** Claude needs to read from or write to an external system (JIRA, Confluence, Figma, GitHub, databases, internal APIs). MCP is a *data source* layer, not a workflow layer — it almost always combines with skills or subagents.

**Don't use when:** the data is already in the local filesystem or already in the conversation, or when a one-off `curl` call would be simpler.

**Setup cost:** medium. Requires the MCP server to exist (or to be written), plus authentication setup.

### Subagent

**Use when:** the task is large enough to pollute the main context, or benefits from parallelism. Examples: scanning 100+ files, running multiple independent research queries, processing a batch of tickets. Subagents run in isolated context and return only a summary.

**Don't use when:** the task is small, sequential, or benefits from the main context's accumulated state.

**Setup cost:** medium. Requires deciding what to delegate and how to summarize the result.

### Hook

**Use when:** a deterministic shell action must run before or after a Claude tool call, every time, without Claude having to decide. Examples: run linter after every file edit, block dangerous bash commands via PreToolUse exit 2, send Slack notification when a long task finishes.

**Strong hook signal:** the user complains about a manual repetitive action with **zero judgment involved** — "every time I save, I have to run X", "I always forget to format before commit", "I keep having to copy-paste this output to Y". These are pure mechanical actions. Hooks were built for exactly this. When you hear this signal, name hooks explicitly even if you also recommend a different primary mechanism — the user should know the option exists.

**Don't use when:** the action requires judgment (use a skill), or when the user is new to Claude Code (hooks have the highest setup cost — start with skills).

**Setup cost:** high. Requires understanding hook event types (PreToolUse, PostToolUse, etc.), shell scripting, and exit code semantics. **Recommend hooks only after the user has built at least one working skill.**

### Plugin (Step 2: distribution)

**Use when:** a working combination of skills/hooks/subagents/MCP needs to be distributed to multiple repos or team members. Plugins package everything for one-command install, version management, and secure secret storage via keychain.

**Don't use when:** the workflow is still being iterated on, or when only one person uses it.

**Setup cost:** medium. Mostly packaging work, not new design.

## Common composition patterns

These are battle-tested combinations. Suggest them by name when the user's situation matches.

### Pattern 1: Slash command + Subagent + Hook

**Shape:** user runs `/long-task arg` → skill kicks off subagent for parallel work → hook fires when subagent completes (notification, validation, cleanup).

**Use for:** batch processing, parallel research, anything where the user wants to fire-and-forget.

### Pattern 2: Auto skill + MCP

**Shape:** Claude detects a domain situation → loads auto skill containing the rules → skill instructs Claude to fetch data via MCP → Claude applies rules to the fetched data.

**Use for:** domain-specific automation that needs live external data. The CPDT JIRA triage classifier is exactly this pattern.

### Pattern 3: CLAUDE.md + Auto skill

**Shape:** CLAUDE.md sets 3–10 universal baseline rules → auto skills add situational depth when their triggers fire.

**Use for:** any non-trivial codebase. CLAUDE.md is the floor; skills are the rooms.

### Pattern 4: User skill as scaffolding, Hook as guardrail

**Shape:** user skill defines the happy-path workflow (`/deploy`) → PreToolUse hook blocks the workflow if a precondition fails (uncommitted changes, failing tests).

**Use for:** workflows where humans need a quick command but the cost of mistakes is high.

## Anti-patterns

Watch for these and push back when you see them.

**"I'll make a skill for this one-time task."** No. Just do the task. Skills have maintenance cost. If it repeats later, build the skill then.

**"Let me put all our company rules in CLAUDE.md."** No. CLAUDE.md is for 3–10 cross-cutting rules. Anything situational becomes an auto skill. A bloated CLAUDE.md dilutes the rules that actually matter — Claude starts ignoring them.

**"I'll start with a hook because hooks are powerful."** No. Hooks have the highest setup cost and the worst failure modes (silent breakage, hard-to-debug exit codes). New users should build a working skill first, then consider whether a hook would replace or augment it.

**"MCP can replace my skill."** No. MCP is a data source. Skills are workflow logic. They live at different layers and almost always combine.

**"Let me design the full system before testing anything."** No. Build the smallest working version first (usually a single skill or just direct conversation). Add layers only when the simpler version proves insufficient.

**"I'll copy-paste the config to share with my team."** No. That's what plugins are for. Manual sharing breaks on the first version mismatch.

**"The user added detail during clarification, so the task is bigger than I thought — let me upgrade the mechanism."** No. Scope creep during clarification is a trap. The user's *original* complaint is the real task; the extra detail is usually wishlist material. See Step 2 of the design flow for how to defend against this.

**"The user gave me a big container of unrelated content — let me match it with one big container mechanism."** No. When the user lumps multiple distinct concerns together (e.g. "put all our docs into CLAUDE.md"), the right move is to *unbundle* them into different mechanisms, not match the bundle with a single oversized mechanism. See `references/successful-patterns.md` → "Three-layer refusal" for how to do this gracefully.

## Design flow

When the user asks for help designing a workflow, follow this sequence. Don't skip steps — but **do skip individual questions when the answer is already obvious from the user's prompt or memory**.

### Step 1: Clarify the task

Step 1 is **diagnosis, not a fixed questionnaire**. You are not filling in a form. You are gathering exactly the information needed to recommend a mechanism, and no more. Different tasks need different questions.

**Two dimensions, independent of each other:**

- **Content** (which variables to ask about) — this should be *dynamic*, chosen based on the task.
- **Format** (how each question is presented) — this should *default to structured select options*, regardless of task.

These two dimensions are often confused. "Dynamic" means you pick *different questions* for different tasks; it does NOT mean you change the question *format*. A structured select with 3–4 pre-built options is faster for users to answer, reduces cognitive load, and produces cleaner data for you to reason about. **Default to select options.** Only fall back to open-ended questions in the specific scenarios listed in `references/successful-patterns.md` → "Adapting clarification format" (primarily: refusal cases where pre-built options would constrain the user's reframing). If you're not sure, use select options — being wrong about format costs the user a few extra clicks; being wrong about content costs a whole wrong recommendation.

**Pacing: ask one question at a time.** Present Q1, wait for the answer, then present Q2 based on what you learned. Do not batch multiple questions into a single message, even if you already know which variables you want to cover. One-at-a-time is not slower — it's actually faster on average because (a) early-exit answers can short-circuit the flow before you ever reach Q2, (b) Q2 can adapt based on Q1's answer instead of being pre-committed, (c) the user's cognitive load per turn is a single decision instead of a form. Batching feels like filling out a questionnaire; one-at-a-time feels like a diagnosis. Pacing is orthogonal to format — each question is still presented as select options, just one at a time.

**Rendering format: use Arabic-numeral lists.** Claude Code's terminal UI renders a list of the shape `1. ... / 2. ... / 3. ...` as an interactive keyboard-selectable menu (the user can press `1`, `2`, `3` or arrow keys to select). Other list styles — bullet lists (`-`), lettered lists (`A) / B)`), mixed forms (`- A)`) — do **not** trigger this UI. They render as plain markdown and force the user to type their answer, which defeats the entire point of using structured select options. **Always use `1. 2. 3.` for clarification options.** Optionally add one short explanation line under each option, indented with three spaces (two-line form). Example:

```
這個任務多久需要做一次？

1. 每次都要
   每次觸發條件出現時都需要執行
2. 偶爾會用到
   視情況需要時才處理
3. 只做這一次
   一次性任務，做完就結束
```

See `references/successful-patterns.md` → "Adapting clarification format" → "Rendering format" for the full list of wrong formats to avoid.

**The variables you might need to know** (pick the ones that matter for *this* task):

- **Frequency** — one-shot, occasional, daily, every-edit? This determines whether automation pays back its setup cost. **In one-at-a-time mode, ask this first.** Rationale: frequency is the fastest early-exit trigger — if the answer is "one-shot", you stop immediately and skip every other question. Motive is conceptually primary (see Core Principle 6), but in a linear flow, asking the question that *might end the flow* before asking the question that *shapes the remaining questions* is the right ordering. Motive still determines *how* you design once you're past the early-exit gate.
- **Motive** — what specific pain or problem made the user ask? Ask this second, once frequency has confirmed there's actually something worth designing. Misdiagnosed motives produce over-engineered solutions, so this variable controls the shape of every question after it.
- **Inputs and outputs** — file paths, ticket IDs, URLs, free text? Knowing the I/O shape narrows the mechanism.
- **Prerequisite maturity** — does the knowledge/rules/data this workflow needs already exist? If not, automation is premature; the prerequisite is the real task.
- **Scope of users** — just this person, a small team, the whole org? Determines whether plugin distribution enters the picture.
- **Existing setup** — for distribution-flavoured questions, what does the current working version look like? What's hardcoded? Where are secrets stored?

**Question selection rules:**

- **Simple tasks need 1–3 questions.** If the prompt is "analyze this CSV", you probably need only "is this one-shot or recurring?". Don't pad.
- **Composition tasks need 4–5 questions.** When the prompt smells like multiple mechanisms (mentions data source + processing + batch + sharing), spend more questions, each locking down one variable that maps to one mechanism.
- **Distribution tasks need different questions entirely.** Don't ask "how often" — ask about hardcoded values, secret storage, and team familiarity. The question content adapts to the task type.
- **Skip any question whose answer is in the prompt or memory.** If the user said "我們團隊", don't ask "is this for a team?". Inference > redundancy.

**Early exit rules:**

Stop asking questions and proceed to a conclusion immediately when:

- The user answers "**one-shot / just this once**" to the frequency question. Conclusion: no mechanism needed, do the task. Don't ask the remaining questions.
- The user reveals that **the prerequisite knowledge or rules don't exist yet**. Conclusion: the prerequisite is the real task. Help them build it first; automation comes later.
- The user's stated motive is **a single concrete pain point** that one small mechanism can clearly solve. Conclusion: propose that one mechanism, skip remaining questions.

When you exit early, briefly explain why you're not asking more questions ("you said this is one-shot, so we don't need to design anything — let me just do it"). This teaches the user the principle by demonstrating it.

### Step 2: Find the minimum viable mechanism

**Before proceeding, sanity-check the original pain point.** If the user's clarification answers expanded the scope beyond their original complaint, you have a choice to make: solve the *original* pain with the smallest mechanism, or solve the expanded scope with a larger one. **Default to the original.** Say something like:

> "Your original problem was [X]. During clarification you also mentioned [Y] and [Z]. I can solve [X] alone with a small [mechanism], and we can add [Y] and [Z] later if they actually become problems. Or I can design for all three now, which means [bigger mechanism]. Which do you prefer?"

This question protects the user from their own scope creep. Most of the time they'll pick the smaller version once they see the trade-off explicitly.

Then default to the cheapest mechanism that could work. The decision tree:

1. Repeats? If no → stop, just do the task.
2. Cross-cutting rule? → CLAUDE.md.
3. Situation-triggered domain knowledge? → auto skill.
4. User-triggered fixed workflow? → user skill (with `/command`).
5. Needs external data? → add MCP to whichever skill above.
6. Large/parallel/context-heavy? → add subagent.
7. Deterministic shell action before/after tool use? → add hook (only if user is comfortable with Claude Code).

**For composition tasks:** unbundle the user's request into distinct concerns, map each concern to one mechanism, and present the mapping as a table (concern → mechanism → trigger). This makes the architecture legible. See `references/successful-patterns.md` → "Composition mapping table" for the canonical format.

### Step 3: Propose an MVP

Describe the smallest version that delivers value. **Explicitly call out what you're *not* building yet.** Example: "Let's start with a user skill that handles one ticket. Once that works, we'll add a subagent to batch 50 tickets."

If the user asked for a batch / bulk / parallel version, **deliberately propose the single-item version first**. Explain that the single-item version validates the design and surfaces bugs early, before the batch version multiplies them. Users almost always agree once you explain the reasoning.

**Distribution workflows are different.** If the task involves packaging an existing setup for others, Step 3 is not "build the smallest version" — it's "list the blockers that must be fixed before distribution is even possible". Hardcoded paths, secrets in config files, personal identifiers — these are blockers, not nice-to-haves. Name them as blockers, explain the consequence of not fixing them ("if we skip this, your teammates' tickets all get tagged as you"), then propose a fix-then-package phased plan. See `references/successful-patterns.md` → "Pre-distribution blockers" for the canonical structure.

### Step 4: Mark upgrade paths

Note where the design can grow later. This sets expectations and prevents regret. Example: "Once you've used this for a week, you might want to add a PostToolUse hook to log every triage decision to a spreadsheet — but that's optional."

Use the canonical phrasing: **"if [future condition], you can [add specific mechanism]"**. This pattern is loose enough not to commit the user to anything, specific enough that they know exactly what door is open. See `references/successful-patterns.md` → "Upgrade path phrasing" for variations.

### Step 5: Distribution

If more than one person will use it, recommend packaging as a plugin once the design stabilizes. Don't suggest plugin packaging during the MVP phase — it's premature optimization.

For team distribution with mixed familiarity (some users know Claude Code, some don't), suggest the **lowest-cost distribution path**: experienced users self-install via README, new users get one walkthrough session. Don't propose elaborate onboarding rituals — the goal is to get the tool into hands, not to run a training program.

## Invocation notes

This skill is invoked by:
- Direct user request (e.g. "help me design a Claude Code workflow", "should I use a hook or a skill?")
- The `/sos` slash command (mnemonic: "Stuck On Setup" / "Save Our Stack")
- Symptoms like "I keep having to manually...", "every time I...", "is there a way to automate..."

When invoked, always start with **Step 1 (Clarify the task)** of the design flow. But remember: Step 1 is diagnosis, not a questionnaire. Ask only the questions that matter for *this* task, skip what's already known, and exit early when the answer becomes obvious.

For canonical examples of what good responses look like — successful refusals, composition mapping tables, blocker structures, upgrade path phrasing — read `references/successful-patterns.md` when you need a concrete template.
