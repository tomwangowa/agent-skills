---
name: understand-repo
description: Use when understanding a repository or subsystem before reading individual files, including its purpose, runtime boundaries, entry points, representative flows, configuration, tests, and reading path.
disable-model-invocation: true
---

# Understand Repo

## Invocation Policy

Run this skill only when the user explicitly invokes `understand-repo`, such as
`/understand-repo` in Claude Code or `$understand-repo` in Codex. A matching task,
a router recommendation, or another skill's suggested reading path does not
authorize invocation. Keep the skill available for manual use.

## Purpose

Use this skill when the user wants to understand an unfamiliar repository before reading individual files or functions.

The goal is not to enumerate every directory or file. The goal is to build a compact, accurate mental model of:

- what the repository does,
- how it is structured,
- where execution starts,
- which modules own which responsibilities,
- how data and control move through the system,
- what configuration and runtime assumptions matter,
- how tests define expected behavior,
- and which files or functions are worth reading next.

This is a read-only comprehension workflow unless the user explicitly asks for code changes.

---

## Inputs

Required:

- repository root or current repository context.

Optional:

- `focus`: a feature, subsystem, workflow, bug area, or architectural concern.
- `depth`: `quick`, `standard`, or `deep`. Default: `standard`.

If the current working directory is clearly the intended repository, use it without asking.

---

## Core Rules

1. Do not start by recursively reading the whole repository.
2. Build the smallest useful active working set.
3. Prefer evidence from code, config, tests, docs, and call sites.
4. Do not confuse directory names with architectural truth.
5. Separate:
   - **Confirmed**: directly supported by repository evidence.
   - **Inferred**: plausible interpretation based on structure and usage.
   - **Unknown**: not established by available evidence.
6. Do not modify code unless explicitly requested.
7. Stop expanding once the repository's important runtime model is clear.
8. Prefer high-signal files over broad enumeration.
9. If the repo contains multiple apps/services/packages, identify them first before explaining details.
10. If generated/vendor/build output exists, exclude it unless it is relevant.

---

## Workflow

### Step 1 — Identify Repository Shape

Inspect only enough top-level structure to answer:

- Is this a monorepo or single application?
- What languages/frameworks are present?
- What are the main apps/packages/modules?
- What build/package systems are used?
- What major runtime artifacts exist?

Look first at high-signal files such as:

- README
- package manifests
- build files
- workspace files
- container/deployment config
- main config files
- source roots
- test roots

Avoid dumping the full file tree.

---

### Step 2 — Establish the System's Job and Boundaries

Open with what the system receives or exposes, the work it performs, and what
result reaches which consumer. Use a short paragraph that makes the operation
concrete; a framework inventory or one compressed sentence is insufficient.
For a library, describe its public API and the application that uses it rather
than inventing a deployed service. If the purpose is unclear, verify entry points
and call sites before explaining it.

Identify the primary runtime and any materially distinct applications, local
runners, experiments, or design proposals. Establish which paths actually connect
in code. Similar directory names or a shared repository do not prove integration.
State the boundary of the explanation when only one subsystem is in scope.

Before module tables or configuration lists, provide an ASCII architecture map
of the relevant owned components and external systems. State whether each arrow
represents a call, data movement, or dependency; label mixed edge kinds or split
views. Mark optional paths and disconnected experiments explicitly. Do not mix
model/type names into a processing chain or portray a proposal as running code.

Follow the map with the concrete walkthrough from Step 5, then expand the module
and configuration details needed to explain it. Investigation order is not the
mandatory presentation order.

---

### Step 3 — Find Entry Points

Locate the major execution entry points.

Examples:

- CLI main
- HTTP server bootstrap
- worker process
- app startup
- framework router
- scheduled job
- consumer
- library public API

For each entry point explain:

- what starts it,
- what it initializes,
- what subsystem it hands control to.

---

### Step 4 — Map Responsibility Boundaries

Identify the architectural units that explain the representative operation.
For each important unit establish what work it owns, what input it receives,
what it passes on, and which caller or consumer relies on it.

Keep execution, shared data definitions, resource/configuration inputs, and
external adapters distinguishable. Explain control decisions at their actual
owner: the algorithm's result, processing status, delivery decision, and message
acknowledgement may be separate outcomes. Inspect the implementation before
claiming success at one boundary guarantees success at another.

Do not enumerate every module or dependency equally. Introduce supporting
modules where they explain a transition in the walkthrough. Use a compact table
only when it makes responsibilities easier to compare after orientation.

---

### Step 5 — Trace One Concrete End-to-End Operation

Choose the representative flow from actual entry points, call sites, tests, or
fixtures. Begin with a concrete request, event, CLI operation, or public API call.
Label synthetic inputs and distinguish executed, code-traced, and illustrative
examples. Do not claim a successful external call from mocks or source inspection.

Trace the input through relevant actors and representations to its final consumer
or effect. Explain each important transition: who validates or transforms the
data, what changes, who makes the decision, and how the next component uses it.
For transformations, show retained or discarded information when consequential.

Continue past core computation to delivery, persistence, acknowledgement, or
other completion behavior when those stages exist. Explain the most consequential
alternate outcome alongside the main path, such as a valid no-result, rejected
input, retry, or skipped delivery. Do not invent transaction, deduplication,
exactly-once, cancellation, or retry guarantees from naming or async syntax.

When there are materially distinct runtime paths, explain their shared parts and
verified differences. Do not assume local tools execute the production orchestration.
For a monorepo, map applications first, then trace the requested or representative
application; do not manufacture one pipeline connecting unrelated packages.
Expand additional flows only when needed to explain a distinct responsibility.

---

### Step 6 — Identify State and External Boundaries

Locate important stateful or external boundaries:

- databases,
- caches,
- queues,
- filesystems,
- external APIs,
- model providers,
- feature flags,
- secrets/config,
- shared state.

Explain where these boundaries are represented in code.

---

### Step 7 — Understand Configuration

Inspect relevant configuration and answer:

- how environments differ,
- which config is runtime-critical,
- what defaults exist,
- what feature flags or provider switches matter,
- where secrets are expected to come from.

Do not expose secret values.

---

### Step 8 — Read Tests as Architecture Evidence

Inspect representative tests to learn:

- expected high-level behavior,
- subsystem boundaries,
- dependency seams,
- important invariants,
- critical edge cases.

Tests often reveal the intended contract more reliably than naming alone.

---

### Step 9 — Identify Important Design Constraints

Look for constraints such as:

- layering rules,
- dependency direction,
- async/concurrency assumptions,
- idempotency,
- retries,
- transaction boundaries,
- serialization contracts,
- compatibility requirements,
- plugin/provider abstractions.

Classify explanations as:

### Confirmed
Supported directly by repository evidence.

### Inferred
Interpretation supported indirectly by structure or usage; intent remains unconfirmed.

### Unknown
Not established.

---

### Step 10 — Produce a Question-Driven Reading Path

Recommend the smallest reading sequence that resolves the reader's remaining
questions. For each file or symbol, state what question reading it answers and
why it follows from the current explanation. Do not require five files or
recommend a module, file, and function that all repeat the same target.

Use `understand-file` for a selected file's role and relationships, or
`understand-function` for a specific contract or branch when deeper exploration
is requested. Do not automatically run both across all recommended targets;
repository orientation should remain bounded.

---

## Explanation Requirements

The workflow is an internal investigation checklist, not twelve mandatory output
sections. Organize the answer around the reader's understanding and focus. Omit
empty sections, repetitive summaries, and exhaustive file/configuration lists.

Start with the system's job and runtime boundaries, the labeled architecture map,
and the representative walkthrough. Only then expand responsibilities,
configuration, external effects, tests, and relevant constraints. Keep source
references near the claims they support.

### Language and scope

- Match the user's language; preserve exact names, paths, identifiers, and values.
- Explain abstractions through concrete behavior. "Data contract" needs what data
  is exchanged by which components; "orchestration" needs who calls what and how
  it handles completion or failure.
- Use connected prose for cause and consequence. Use tables for actual mappings
  or comparisons and lists for parallel items, not compressed sentence fragments.
- Give consequential transitions more space than imports or technology lists.
  Remove repetition before shortening the explanation's causal relationships.
- Separate running code, comments, approved target designs, and proposals.
  Code checked into an experiment is not proof of production integration.
- Keep Confirmed, Inferred, and Unknown identifiable in context; dedicated headings
  are optional. Do not turn observed implementation into an unchangeable requirement
  or invent design motives, deployment state, throughput, quality, or cost claims.
- Configuration defaults and declared deployment templates are not observed live
  values. Explain precedence and the few switches that alter the traced flow;
  do not inspect secret values or enumerate unrelated environment variables.
- Explain resource files when they change behavior, not merely as repository
  decoration. State which code loads them and whether overrides change resolution.
- For state and I/O, explain who reads or changes it and under which conditions.
  Distinguish computation, optional logging/export, and required delivery effects.
- Keep health/liveness signals separate from demonstrated task completion. Treat
  timeout, cancellation, and background work as distinct unless code proves otherwise.
- Distinguish tests inspected from commands executed. State what assertions and
  mocks establish, which paths were not exercised, and any failures encountered.
  Do not present selected passing tests as a passing full suite.

### Flexible output

Choose headings only when they help navigation. The answer must establish runtime
position and a representative operation, then retain the important responsibilities,
external/state boundaries, configuration assumptions, and test/verification limits.
Adjust the depth for workers, libraries, CLI tools, web applications, or monorepos.

Avoid a concluding "five things to remember" that repeats the opening. Reading
suggestions should answer specific open questions, without an additional duplicate
module/file/function drill-down list. Do not add quizzes unless requested.

## Final Writing Pass — sepia

After repository investigation and drafting, use the available `sepia` skill to
review and revise the explanation. Read its SKILL.md and the references required
by its non-fiction routing; do not merely mention the skill or assume its rules.
This pass edits the explanation, not the repository.

Check structure before wording: can the reader identify the system's job, the
runtime boundaries, the diagram's edge meanings, and the walkthrough's actors?
Diagnose
unclear abstractions, unexplained consequences, and repeated sections before
editing. Keep the defect list internal unless the user asks for an editing report.

Preserve the verified facts during revision: exact identifiers, paths, numbers,
field values, conditions, test results, and uncertainty labels. Do not invent
motives, simplify away branch conditions, or turn an inference into a fact.
After revision, compare changed claims and diagram relationships with the
repository evidence before returning the answer.

If `sepia` is unavailable, disclose the missing writing pass briefly and apply the
Explanation Requirements directly. Do not silently claim it ran, install a skill,
or block an otherwise supported repository explanation.

## Examples

These are illustrative task patterns, not claims about an existing repository.

### Example 1 — A worker repository with an experiment

Request: "Help me understand this repository before reading its source files."

Expected approach: establish the worker's input and consumer, draw message flow
through processing and delivery with optional effects labeled, and place a
standalone experiment outside the runtime boundary if code does not connect it.
Walk a fixture from input to acknowledgement or retry. Explain the difference
between a computed result and successful delivery before listing every module.
Keep code defaults separate from unverified deployment values.

### Example 2 — A library or multi-package repository

Request: "Explain this repository, focusing on the parser package."

Expected approach: identify public API entry points and package boundaries, then
trace a representative parse call from input to returned data or error. Show
shared definitions as dependencies rather than active stages. Inspect caller
usage if available, and state when no host application can be established. Avoid
invented queues, deployment, storage, or one flow connecting unrelated packages.

---

## Depth Modes

### quick

Inspect:

- top-level structure,
- primary README/config,
- main entry point,
- one representative flow,
- one representative test.

Keep the architecture map and walkthrough focused on orientation, with only
the most consequential boundaries and configuration assumptions. Retain the
final writing pass; this mode narrows investigation breadth, not clarity.

### standard

Use the full workflow.

### deep

Additionally inspect:

- multiple runtime entry points,
- architecture/design docs,
- more representative tests,
- config variants,
- alternate implementations,
- relevant version-control context if available.

Only expand when it materially improves understanding.

---

## Stop Rule

Stop expanding repository context once you can explain with evidence:

- repository purpose,
- major runtime entry points,
- module responsibilities,
- one representative end-to-end flow,
- external/state boundaries,
- important configuration,
- and the best next files/functions to inspect.

Do not keep scanning simply because more files exist.
