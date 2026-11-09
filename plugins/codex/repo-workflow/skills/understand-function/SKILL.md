---
name: understand-function
description: Use when explaining one function or method in repository context, including its caller, contract, transformations, side effects, branches, tests, and modification constraints.
disable-model-invocation: true
---

# Skill: understand-function

## Invocation Policy

Run this skill only when the user explicitly invokes `understand-function`, such as
`/understand-function` in Claude Code or `$understand-function` in Codex. A matching task,
a router recommendation, or another skill's suggested reading path does not
authorize invocation. Keep the skill available for manual use.

## Purpose

Use this skill when the user wants to understand one function or method inside a repository.

The goal is to establish the function's true behavioral contract in context:

- why it exists,
- who calls it,
- what inputs callers actually provide,
- what it returns,
- what side effects it causes,
- how branches change behavior,
- what downstream dependencies do,
- what tests establish,
- and what must remain true if the function is modified.

This is a read-only comprehension workflow unless the user explicitly asks for code changes.

---

## Inputs

Required:

- `file_path`: repository-relative path containing the target function.
- `function_name`: function or method name.

Optional:

- `focus`: particular behavior, branch, bug, input, or design question.
- `depth`: `quick`, `standard`, or `deep`. Default: `standard`.

If the target function can be identified unambiguously from the current context, do not ask the user to repeat it.

---

## Core Rules

1. Do not explain only the function body.
2. Search for callers before finalizing the explanation.
3. Inspect the relevant types, dependencies, and tests.
4. Prefer actual call sites over hypothetical usage.
5. Trace a concrete example when it materially improves understanding.
6. Do not modify code unless explicitly requested.
7. Separate:
   - **Confirmed**
   - **Inferred**
   - **Unknown**
8. Do not infer requirements purely from names.
9. Do not list speculative edge cases as if they are supported behavior.
10. Focus on the smallest context that establishes the function's contract.

---

## Workflow

### Step 1 — Identify the Function in Context

Read the target function and enough surrounding code to understand:

- enclosing class/module,
- relevant local state,
- nearby helper functions,
- decorators / annotations,
- return types,
- exceptions.

Then search the repository for:

- callers,
- tests,
- interface declarations,
- overridden / overriding implementations,
- important dependencies called by the function.

---

### Step 2 — Establish Its Role Before Its Mechanics

Open with the surrounding operation: what the caller is trying to accomplish,
what input it has at this point, and what the next consumer needs. Explain the
function's contribution in a short paragraph using the actual caller and consumer.
A phrase such as "extracts and deduplicates text" is insufficient unless the
reader can tell who needs the text and how it affects the next step.

Provide a focused ASCII diagram of the verified relationships before detailing
parameters or branches. State whether arrows represent calls, data movement, or
execution order. Label mixed edge kinds or use separate diagrams. Show input
preparation and result consumption outside the target's boundary; do not assign
caller filtering, retries, or downstream side effects to the target function.
For repeated conditional calls, show the caller's decision when it materially
changes what reaches the target. Avoid forcing every function into a linear
pipeline: callbacks, recursion, and shared helpers may need a different shape.
If there is no caller, say so and explain only the supported local behavior.

Introduce one representative caller-context walkthrough from Step 7 immediately
after the diagram. Then expand the contract and implementation details that
explain that example. Keep investigation order separate from presentation order.

---

### Step 3 — Establish the Contract

#### Inputs

For each important parameter explain:

- type / shape,
- where it comes from,
- assumptions,
- optionality,
- normalization already performed by the caller,
- validation expected inside this function.

#### Output

Explain:

- return type / shape,
- possible variants,
- null/empty/error behavior,
- who consumes the result.

#### Side Effects

Check explicitly for:

- database writes,
- state mutation,
- cache changes,
- API calls,
- filesystem changes,
- event publication,
- logging,
- metrics,
- tracing,
- global/shared state.

If there are none, say so.

---

### Step 4 — Inspect Callers

Find materially distinct call sites.

For each major caller explain:

- when it calls the function,
- what arguments it passes,
- how it handles the result,
- what assumptions it makes.

If many callers are equivalent, summarize them as a group.

If callers disagree about assumptions, call this out.

---

### Step 5 — Explain Execution as Logical Steps

Rewrite the function behavior into conceptual steps.

Example:

1. Normalize input.
2. Reject invalid state.
3. Build candidate set.
4. Score candidates.
5. Select result.
6. Persist / emit result.
7. Return.

For each step explain:

- what changes,
- why the step exists,
- which dependency participates,
- what invariant it preserves.

Do not translate syntax mechanically.

---

### Step 6 — Map Decision Points

Identify meaningful branches.

Use a compact representation when helpful:

```text
condition A?
├─ yes → path 1
└─ no
   └─ condition B?
      ├─ yes → path 2
      └─ no  → fallback
```

For each branch explain:

- trigger,
- behavior,
- returned value / side effect,
- downstream consequence.

Include early returns and exception paths.

---

### Step 7 — Trace a Concrete Example in Caller Context

Prefer a representative input from tests, actual call sites, or fixtures;
otherwise label the example as synthetic. Trace what the caller prepares or
selects, what is actually passed to the target, the important intermediate values,
and how the consumer uses the return value. Show only stages that exist.

For transformations, make before/after differences visible with a small table,
code block, or paired values. State what information is retained, reordered,
converted, combined, or discarded, and why that matters to the next consumer.
Keep observed behavior separate from an unproven design motive.

A direct call with an arbitrary input proves only the helper's local behavior.
Do not present a broad direct-call example as a real production input if the
caller would filter it first. If both views are needed, label "direct function
call" and "caller-selected input" distinctly. Explain the caller's selection or
short-circuit policy before drawing conclusions about the full path.

Label examples as executed, traced from code, or illustrative and unexecuted.
A hypothetical caller response is not an observed result. Do not invent domain
values, expected outputs, or successful dependency calls. For functions with no
caller, use a clearly labeled direct-call example without inventing a consumer.

---

### Step 8 — Explain Important Dependencies

For each significant downstream call answer:

> Why does this function need this dependency?

Avoid recursively explaining entire dependencies unless necessary.

If understanding one dependency is essential, inspect only the relevant symbol.

---

### Step 9 — Read Tests as Contract Evidence

Inspect tests for this function or behavior.

Extract:

- expected results,
- error cases,
- boundary conditions,
- side effects,
- ordering assumptions,
- mocks that reveal architectural boundaries.

Answer:

> What behavior is explicitly protected by tests?

Also state what important behavior is *not* covered if that is evident.

---

### Step 10 — Investigate Non-Obvious Logic

If the function contains surprising or indirect logic:

1. inspect callers,
2. inspect tests,
3. inspect comments,
4. inspect related implementations,
5. inspect version-control context if available.

Then classify:

### Confirmed
Directly supported by evidence.

### Inferred
Interpretation supported indirectly by callers or structure; design intent remains unconfirmed.

### Unknown
Cannot be established.

Do not turn inferred rationale into historical fact.

---

### Step 11 — Identify the Behavior That Must Remain True

Identify the observable behavior relied on by callers, tests, or interfaces.
Separate current implementation behavior from an approved requirement: an
observed grouping order is not automatically a business rule that must never
change. If the intended requirement is unknown, state the uncertainty.

For a transformation, relate its guarantees and information loss to the
consumer's needs. For a stateful function, explain the state transition and
observable effects. Do not force one universal invariant; include only the
constraints needed to understand the function or modify it safely.

---

## Explanation Requirements

Use the workflow as an internal investigation checklist, not fourteen mandatory
output sections. Organize the answer around the reader's understanding and
requested focus; omit empty or repeated sections.

Start with the caller's operation and the function's role, the labeled ASCII
diagram, and the caller-context walkthrough. Then explain important contract,
branch, dependency, and test evidence. Put references near supported claims.

### Language and detail

- Match the user's language and retain exact identifiers and field values.
- Explain abstract terms through concrete actors and behavior on first use.
  "Deduplication" needs what is compared and what disappears; "priority" needs
  who selects a path and what happens to lower-priority input.
- Explain meaningful behavior through its trigger, owner, and consequence.
  Keep caller guarantees, target checks, and consumer actions distinguishable.
- For returned text or data, show its shape and how the next step uses it.
  Explain transformations and information loss before listing edge cases.
- Prefer connected prose for causality. Use tables for mappings and before/after
  comparisons, and lists for parallel items rather than unexplained fragments.
- Remove repetition before shortening an explanation's causal relationships.
  Give unusual or consequential behavior more space than routine syntax.
- Keep Confirmed, Inferred, and Unknown distinguishable in context; standalone
  headings are optional. Neither names nor typical patterns prove design intent.
- Separate local behavior from reachability in real callers. A supported branch
  might never receive an input through the current production path.
- State side effects and exception ownership explicitly. Explain whether the
  target changes input or state, throws, catches, or returns a fallback, and
  inspect the caller before claiming retry or recovery behavior.
- Distinguish tests inspected from tests executed. A direct unit test does not
  establish caller selection or end-to-end behavior. Report only observed command
  results and say which important behavior the assertions do not cover.

### Flexible output

Choose headings only when they improve navigation. Preserve the facts needed to
understand the actual input, output, side effects, and meaningful branches, without
repeating them under separate contract, execution, dependency, and invariant
headings. Include grounded modification constraints and remaining uncertainty.

Next-reading suggestions should resolve a specific unanswered relationship.
Knowledge-check questions are optional unless requested; they cannot substitute
for explanation. Do not require a fixed number of invariants or reading targets.

## Final Writing Pass — sepia

After repository investigation and drafting, use the available `sepia` skill to
review and revise the explanation. Read its SKILL.md and the references required
by its non-fiction routing; do not merely mention the skill or assume its rules.
This pass edits the explanation, not the repository.

Check structure before wording: can the reader identify the system's job, the
function's role, the diagram's edge meanings, the caller/target boundaries,
and the walkthrough's actors? Diagnose
unclear abstractions, unexplained consequences, and repeated sections before
editing. Keep the defect list internal unless the user asks for an editing report.

Preserve the verified facts during revision: exact identifiers, paths, numbers,
field values, conditions, test results, and uncertainty labels. Do not invent
motives, simplify away branch conditions, or turn an inference into a fact.
After revision, compare changed claims and diagram relationships with the
repository evidence before returning the answer.

If `sepia` is unavailable, disclose the missing writing pass briefly and apply the
Explanation Requirements directly. Do not silently claim it ran, install a skill,
or block an otherwise supported function explanation.

## Examples

These are illustrative task patterns, not claims about an existing repository.

### Example 1 — A text-conversion helper

Request: "Explain `events_to_text()` in `app/selector.py`."

Expected approach: identify the operation that consumes the text, inspect which
rows the caller passes, and draw selection, conversion, and consumption with
boundaries labeled. Walk one caller-selected fixture through conversion. If the
helper groups or deduplicates rows, show the resulting order and information
lost. A separate mixed-row direct-call example must not imply all rows reach the
helper in the production path. Do not assert the function improves prompt quality
unless an evaluation establishes that claim.

### Example 2 — A function with retry ownership

Request: "Explain `process_job()` in `app/worker.py`, especially failures."

Expected approach: show who calls the function and who handles its result or
exception. Walk a verified failure path, distinguishing a thrown exception from a
returned failure value. Explain any retry, acknowledgement, or state change at
its actual owner. A target-only mock test cannot prove the caller retries, and
no retry branch may be invented from the function name.

---

## Depth Modes

### quick

Inspect:

- target function,
- direct caller(s),
- direct dependencies,
- one relevant test if available.

Keep the explanation focused on the caller, function role, diagram, brief
walkthrough, and consequential contract. Retain the final writing pass; this
mode narrows investigation breadth without omitting causal explanation.

### standard

Use the full workflow.

### deep

Additionally inspect:

- all materially distinct callers,
- broader behavior tests,
- interface hierarchy,
- alternate implementations,
- relevant configuration,
- version-control context if available.

---

## Stop Rule

Stop expanding context when you can explain with evidence:

- why the function exists,
- who calls it,
- its input/output contract,
- meaningful side effects,
- branch behavior,
- downstream dependencies,
- and the invariant that must survive modifications.

Do not recursively explore unrelated implementation details.
