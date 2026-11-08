---
name: review-convergence-gate
description: Use when repeated code review, doc review, design spec review, implementation plan review, or multi-agent review loops need severity gates, stop conditions, and implementation-readiness verdicts to prevent over-review, reviewer drift, duplicate findings, minor/nit churn, or infinite Claude/Codex/Gemini cycles.
---

# Review Convergence Gate

## Purpose

Use this skill as a guardrail before invoking reviewers or when a review loop has started to sprawl. It does not replace `code-review-*` skills. It constrains what reviewers are allowed to report and decides whether the work is ready to move from review to implementation.

Core rule:

```text
The goal is not "no reviewer can find anything."
The goal is "no unresolved blocker remains, major issues are bounded, and implementation can start without guessing core design."
```

## Mode Selection

Choose exactly one mode before asking another agent to review.

| Mode | Use when | Allowed findings |
|---|---|---|
| `normal-review` | First or second pass on a rough artifact. | Blocker, Major, Minor, Nit, but each must say whether it blocks coding. |
| `convergence-review` | Third pass or later, or after multiple agents already reviewed. | Blocker and Major only. Suppress Minor/Nit/Future ideas. |
| `final-gate` | The user asks whether to stop reviewing and start implementation. | Blocker only, plus final verdict. |

Default to `convergence-review` when the user mentions repeated Claude/Codex/Gemini reviews, over-review, review loops, or "can we stop?"

## Severity Definitions

Use these definitions consistently.

- `Blocker`: implementation would be unsafe, impossible, or likely wrong without fixing it. Examples: API contract contradiction, data loss path, migration cannot run, security boundary missing, core flow undefined, test plan cannot verify the main behavior.
- `Major`: should be resolved before or during the first implementation PR, but the fix is bounded and does not require re-opening the architecture. Examples: unclear owner, missing rollback step, incomplete error branch, misleading pseudo-code.
- `Minor`: useful improvement that should not block coding. Suppress in `convergence-review` and `final-gate`.
- `Nit`: wording, formatting, naming preference, extra diagram, or polish. Always suppress unless the user explicitly asks for editorial review.

When uncertain between severities, ask: "Would a competent implementer likely build the wrong thing if this remains?" If yes, raise severity. If no, downgrade or suppress.

## Suppression Rules

Do not report these in `convergence-review` or `final-gate`:

- Wording polish.
- Naming preference.
- Extra diagrams or tables.
- Alternative architecture if the current one is safe and implementable.
- Observability, analytics, or future improvements unless required for release validation.
- Already-known open questions that are explicitly documented with an owner.
- A concern that depends on changing the current milestone scope.
- A duplicate of a previous finding unless the current document still contradicts itself.

## Required Reviewer Prompt

When invoking Claude, Codex, Gemini, or a subagent reviewer, include this block:

```text
Use review-convergence-gate in <MODE>.

Review only the provided scope. Deduplicate known issues.

Allowed findings:
- <MODE RULES>

Do not list Minor, Nit, style, wording, extra-diagram, or future-improvement comments unless they are required to make implementation safe.

For each finding, include:
- Severity: Blocker or Major
- Location: file and line
- Issue
- Impact
- Minimal required fix
- Must fix before coding: Yes/No

End with:
- Verdict: PASS / PASS_WITH_MAJOR_COMMENTS / BLOCK
- Stop recommendation: Stop review / One targeted pass / Continue review
- Reason
```

For `final-gate`, replace the allowed findings line with:

```text
Only list Blockers. If there are no Blockers, do not list Major/Minor/Nit. Say whether implementation can start.
```

## Verdict Rules

- `BLOCK`: one or more Blockers remain. Do not start implementation except for a spike to resolve the blocker.
- `PASS_WITH_MAJOR_COMMENTS`: no Blockers, but one or more Major issues should be fixed or explicitly assigned before implementation.
- `PASS`: no Blockers and no pre-implementation Major issues. Stop general review and start implementation or validation.

Do not use "PASS" if the reviewer has not checked the actual files or diff.

## Stop Conditions

Recommend stopping review when all are true:

1. Two independent review passes found no Blocker, or the current `final-gate` found no Blocker.
2. Remaining Major issues are fewer than three and have owner, phase, or a bounded fix.
3. The artifact answers the core implementation questions:
   - what files or modules change
   - how data flows
   - how errors are handled
   - how compatibility or rollback works
   - what tests prove success
   - what remains explicitly out of scope
4. Remaining comments are Minor, Nit, future improvement, or already-documented open questions.

Recommend one more targeted pass only when a specific topic still carries risk, such as "DB migration only", "API wire contract only", or "test plan only". Do not recommend another general review if the stop conditions are met.

## Handling Review Results

When the user brings back review findings:

1. Classify each finding as `Blocker`, `Major`, `Minor`, `Nit`, `Duplicate`, or `False Positive`.
2. Patch only Blockers and Majors by default.
3. Do not patch Minor/Nit unless the user explicitly asks.
4. Convert unresolved but non-blocking concerns into open questions with owners instead of expanding the document indefinitely.
5. After patching, run at most one targeted re-review for the changed risk area.

If a reviewer reports more than ten findings after multiple rounds, first deduplicate and severity-gate them before patching.

## Examples

### Example 1: Repeated Design Review

User asks:

```text
Claude, Codex, and Gemini have reviewed this spec many times. Can we stop?
```

Use `final-gate`. Ask one reviewer:

```text
Use review-convergence-gate in final-gate.
Review these two files only. Only list Blockers. If there are no Blockers, say PASS and explain whether implementation can start.
```

Expected output shape:

```text
Verdict: PASS_WITH_MAJOR_COMMENTS
Blockers: None
Majors:
1. ...
Stop recommendation: Stop general review. Fix the two Major issues during the first implementation PR.
```

### Example 2: Third Review Pass

User asks:

```text
Run another code review after the latest fixes.
```

Use `convergence-review` unless the user explicitly wants editorial polish.

```text
Use review-convergence-gate in convergence-review.
Only report Blocker and Major issues. Suppress Minor, Nit, future-improvement, naming, and extra-documentation suggestions.
```

## Anti-Patterns

Stop and reframe when you see these:

- A reviewer says "consider also..." without showing implementation risk.
- A reviewer repeats an already-documented open question.
- A patch is made only to satisfy one agent's wording preference.
- Each new review creates new non-blocking scope.
- The artifact becomes longer but not more implementable.

In these cases, switch to `final-gate`.
