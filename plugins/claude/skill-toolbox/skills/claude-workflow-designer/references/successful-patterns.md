# Successful Response Patterns

This file contains canonical templates for high-quality workflow design responses. Read it when you need a concrete example of how to structure a particular kind of answer.

These patterns are extracted from real test cases. Each one solves a specific failure mode that generic responses fall into.

---

## 1. Three-layer refusal

**When to use:** the user proposes putting unrelated content into a single oversized container (e.g. "let me put all our docs into CLAUDE.md", "let me make one giant skill for everything"). You need to refuse without making them feel attacked.

**Structure:**

**Layer 1 — Name the problem and give the reason:**

> "[Doing X] will backfire. Reason: [mechanism] is designed for [original use case]. What you're describing exceeds that — Claude will start ignoring the rules, which makes the most important ones fail. **This is a known design constraint, not a flaw in how you wrote it.**"

The last sentence is critical. It removes blame from the user and puts it on the mechanism. Without this sentence, the user feels criticized; with it, they feel informed.

**Layer 2 — Reframe the problem:**

> "Your real problem vs. the solution you proposed:
>
> Real problem: [the underlying pain, stated in one sentence].
>
> This problem has a more precise solution that doesn't require [the bundled approach]."

This layer accepts that the user has a legitimate pain point, but rejects their proposed solution. Critical: don't argue with the pain, only with the solution.

**Layer 3 — Offer a better alternative:**

Show a composition mapping table (see pattern 2) that unbundles their request into separate concerns, each handled by the right mechanism.

**Example trigger phrases:**

- "I want to put all our [X, Y, Z, W] into CLAUDE.md"
- "Can I make one big skill that does [unrelated thing 1] and [unrelated thing 2]?"
- "Let's stuff everything into [single mechanism]"

---

## 2. Composition mapping table

**When to use:** the user's request contains multiple distinct concerns that need different mechanisms. Use a three-column table to make the architecture legible.

**Structure:**

| Content | Where it goes | Trigger |
|---|---|---|
| [Concern 1] | [Mechanism] | [How it activates] |
| [Concern 2] | [Mechanism] | [How it activates] |
| ... | ... | ... |

**Rules for the table:**

- **Always leave a place for the user's original idea, even if shrunk.** If they wanted CLAUDE.md, leave 2–3 rules in CLAUDE.md so they have a face-saving "you weren't completely wrong" outcome.
- **Every row needs a specific trigger description, not "automatic" or "manual".** Write triggers as "Claude detects X" or "user runs /command" — specific language teaches the user how each mechanism works.
- **Order rows from cheapest mechanism to most expensive.** CLAUDE.md → auto skill → user skill → MCP → subagent → hook → plugin. This visually reinforces the "start with the lowest setup cost" principle.

**For external data sources, prefer "live fetch via MCP" over "copy into skill".** A skill containing copied API documentation goes stale the moment the documentation changes. An auto skill that calls an MCP server stays fresh forever. Make this distinction explicit when relevant.

---

## 3. Pre-distribution blockers

**When to use:** the user wants to package an existing personal setup for team distribution. You discover during clarification that the setup has hardcoded values, secrets in config files, or personal identifiers.

**Structure:**

Before entering Step 2, insert a section called **"Pre-distribution blockers"** (or "前置封鎖點" in Chinese contexts). For each blocker:

- **Name the blocker concretely.** "API token hardcoded in settings.json (high risk)" not "secret management concerns".
- **Explain the consequence in one sentence.** "If this file gets synced to a repo or someone else's machine, your JIRA token leaks." Concrete consequences are more persuasive than abstract warnings.
- **State that the blocker must be fixed before distribution.** Use the word "must" — this is not a suggestion.

Then split the design into phases with explicit labels:

- **Phase 1 — Fix, don't distribute.** All blocker fixes happen here. No packaging yet.
- **Phase 2 — Package as plugin.** Only after Phase 1 completes.
- **Phase 3 — Distribute to teammates.** Differentiate by familiarity (see pattern 5).
- **Phase 4 — Future upgrades** (optional, mark as "now: don't do").

**Why phases matter:** they prevent the user from skipping straight to packaging an unsafe setup. The phase labels enforce ordering.

**Tone note:** use engineer language, not consultant language. "Blocker" not "consideration". "Must fix" not "should consider". "Will leak" not "may have privacy implications". Engineers respond to direct language; soft language gets ignored.

---

## 4. Upgrade path phrasing

**When to use:** at the end of any design response, to mark future possibilities without committing the user to them.

**Canonical pattern:**

> "If [specific future condition], you can [add specific mechanism]."

**Examples:**

- "If this becomes weekly, you can wrap it in a `/analyze-csv` user skill."
- "Once you've used the single-ticket version for a week, you can add a subagent to handle 50 tickets at once."
- "If the team grows past 5 people, you can package this as a plugin for one-command install."
- "When you're ready for stricter enforcement, you can add a PreToolUse hook that blocks commits with unformatted code."

**Why this phrasing works:**

- The "if" is loose — no commitment.
- The condition is concrete — the user knows exactly when to come back.
- The mechanism is named — the user knows exactly what door is open.
- The phrasing implies "this is normal growth", not "you should have done this from the start".

**Anti-pattern to avoid:** "You might want to consider potentially looking into adding..." Vague futures don't help anyone.

---

## 5. Mixed-familiarity distribution

**When to use:** the user wants to share something with a small team where some members are Claude Code experienced and some are new.

**Structure:**

- **Experienced users:** self-install via README. One link, done.
- **New users:** offer one synchronous walkthrough where you (the user) sit with them while they run `claude plugin install ./path`.

**What to avoid:**

- Designing a "training program" or "onboarding session" — this is a 5-person rollout, not a corporate launch.
- Writing a long step-by-step tutorial — the experienced users won't need it and the new users will tune out.
- Splitting into "phase 1: experienced users, phase 2: new users two weeks later" — there's no benefit to delaying the new users; they should get it the same week.

**Principle:** distribution mechanism cost should be proportional to team size. 5 people = 1 README + 2 walkthroughs. 50 people = consider docs and a Slack channel. 500 people = consider a real plugin marketplace listing.

---

## 6. Refusing batch / bulk requests in favor of single-item MVP

**When to use:** the user explicitly asks for a batch version ("process 50 tickets at once", "scan all 200 files", "bulk update everything") on the first design pass.

**Structure:**

> "**Don't build the batch version yet.** The smallest version should be: [a working single-item version]. Reasons:
>
> 1. The single-item version validates the design with cheap iterations.
> 2. Bugs in the single-item version multiply in the batch version.
> 3. Once the single-item version works, adding batch support is a small extension."

Then propose phased work:

1. Build single-item version
2. Verify it works on real input
3. Add subagent / batch wrapper

**Critical: refuse the batch request even though the user asked for it.** The user usually agrees once you explain why. They asked for batch because that's their end goal — they didn't realize the single-item version is the right starting point.

---

## 7. Adapting clarification format to the task

**Default: always use structured select options.** Open-ended questions should be the rare exception, not a tool in regular rotation. Select options are almost always better because they're faster to answer, reduce user cognitive load, produce cleaner data, and visibly narrow the decision space in a way that teaches the user what variables matter.

**The only legitimate reasons to use open-ended questions:**

1. **The user needs to describe a concrete pain point in their own words.** Example: "what specifically goes wrong when you skip this step?" — you need their actual language, not pre-built options.
2. **You're about to refuse or reframe the user's proposal and pre-built options would constrain the reframing.** Example: in a three-layer refusal (pattern 1), you sometimes need the user to articulate their real motive before you can redirect them. Pre-built options would funnel them back into the wrong frame.
3. **The answer space is genuinely open-ended and enumerating options would miss the point.** Example: "paste the error message you're seeing" — no select can replace this.

**That's the entire list.** Three scenarios. Everything else uses select options.

**If you catch yourself reaching for open-ended questions because:**

- "The task feels complex" → use select options anyway. Complex tasks benefit *more* from structure, not less.
- "I want to seem flexible" → flexibility is a content decision (which questions to ask), not a format decision (how to present them).
- "The user seems sophisticated" → sophisticated users appreciate fast input even more than beginners.
- "I'm not sure what options to put" → that's a signal you haven't thought hard enough about the variable. Think again, then write 3–4 options.

**Hybrid approach (when in doubt):** ask all the structured questions first via select options, then end with *one* open-ended catch-all like "anything else I should know?". This captures surprises without sacrificing the speed of structured questions for the main flow.

**Red flag:** if your response contains more than one open-ended question in a row, you're probably doing it wrong. Stop, convert the rest to select options, and continue.

**Pacing: one at a time, not batched.** Format (select vs. open) and pacing (one question per message vs. multiple) are orthogonal — don't confuse them. Even when every question uses select options, you should still present them *one at a time*, waiting for the user's answer before showing the next question. Reasons:

- **Early exit works.** If Q1 is "frequency" and the user picks "one-shot", you stop there. Batching Q1–Q3 means the user stares at Q2 and Q3 that will be thrown away.
- **Q2 can adapt to Q1's answer.** If Q1 reveals a distribution context, Q2 becomes "how are secrets stored?" instead of a generic "how often?". Batching pre-commits you to questions that may no longer fit.
- **Lower cognitive load per turn.** One select with 3–4 options is faster to answer than three selects stacked in one message.
- **Matches conversational rhythm.** Batching feels like a form; one-at-a-time feels like a dialogue.

**Anti-pattern:** presenting Q1, Q2, Q3 as a numbered list in one message with a combined input box ("Q1: A, Q2: C, Q3: C"). This is a questionnaire, not a diagnosis. Even if the format of each question is a select, the batched presentation breaks early exit and adaptive follow-up. A second common anti-pattern: using bullet lists (`-`) or lettered options (`A)`, `B)`) for the choices — these do not trigger Claude Code's interactive menu UI. See "Rendering format" below.

**The only exception:** when you are *certain* all questions are independent AND all answers will be needed regardless of what the user picks (rare). When in doubt, go one at a time.

## 7a. Rendering format: triggering Claude Code's interactive menu

**When to use:** every time you present select options during clarification (which should be almost every clarification question — see the default rule above).

**The rule:** use Arabic-numeral lists (`1. 2. 3.`). Claude Code's terminal UI detects this shape and renders it as a keyboard-selectable menu with a `Type something` / `Chat about this` fallback row. Any other list style renders as plain markdown and forces the user to type.

**Correct format (two-line form, with indented explanation):**

```
這個任務多久需要做一次？

1. 每次都要
   每次觸發條件出現時都需要執行
2. 偶爾會用到
   視情況需要時才處理
3. 只做這一次
   一次性任務，做完就結束
```

The explanation line is indented with exactly three spaces (matching the width of `1. `). You can omit the explanation when the option is self-explanatory, but prefer including it — it helps the user pick faster.

**Wrong formats (all of these render as plain markdown, no interactive UI):**

- Bullet list:
  ```
  - 每次都要
  - 偶爾會用到
  - 只做這一次
  ```
- Lettered list:
  ```
  A) 每次都要
  B) 偶爾會用到
  C) 只做這一次
  ```
- Mixed bullet + letter (the worst of both worlds):
  ```
  - A) 每次都要
  - B) 偶爾會用到
  - C) 只做這一次
  ```
- Arabic numbers without period (`1)` instead of `1.`) — unreliable, use `1.`

**Why this matters:** the entire reason to use select options is to let the user answer with one keystroke. A correctly-rendered menu lets them press `1` and move on; a plain-markdown list forces them to type out the answer, which is slower than answering a well-worded open-ended question would have been. Getting the format wrong undoes the benefit of using structured options in the first place.

---

## 8. The "spoiler" preview for refusal cases

**When to use:** the user's request contains an obvious anti-pattern, but you still want to ask clarification questions before delivering the refusal.

**Pattern:** end the clarification message with a one-line spoiler that hints at the eventual refusal:

> "Answer these questions first, then I can help you design the right approach. **(Spoiler: CLAUDE.md is probably only part of the answer, not the whole thing.)**"

**Why this works:**

- Sets expectations early — the user isn't blindsided when the refusal comes
- Uses humor ("spoiler") to soften what would otherwise feel like an ambush
- Doesn't actually refuse yet — leaves room for the user to provide context that might change your mind
- Demonstrates that you've already noticed the problem, which builds trust

**When NOT to use:** if you're not sure yet whether the user's approach is wrong. The spoiler should be a confident preview, not a guess.
