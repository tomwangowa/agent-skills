---
name: understand-file
description: Use when explaining a source file in repository context, including its architectural role, callers, data flow, tests, and modification constraints.
---

# Skill: understand-file

## Purpose

Use this skill when the user wants to understand a specific source file inside a repository.

The goal is not to translate code line by line. The goal is to build an accurate mental model of:

- why the file exists,
- where it sits in the architecture,
- who calls or imports it,
- what it depends on,
- how data and control flow through it,
- what tests establish as its contract,
- and what a developer must understand before modifying it.

This is a read-only comprehension workflow unless the user explicitly asks for code changes.

---

## Inputs

Required:

- `file_path`: repository-relative path of the target file.

Optional:

- `focus`: a specific concern, feature, bug, class, data flow, or architectural question.
- `depth`: `quick`, `standard`, or `deep`. Default: `standard`.

If `file_path` is missing but the target is unambiguous from the current conversation, use it.
Otherwise ask only if the target cannot be identified safely.

---

## Core Rules

1. Do not explain the file in isolation.
2. Search the repository before explaining the implementation.
3. Prefer repository evidence over assumptions.
4. Do not modify code unless explicitly requested.
5. Do not mechanically explain every line.
6. Separate:
   - **Confirmed**: directly supported by code, tests, config, docs, or repository references.
   - **Inferred**: plausible interpretation based on architecture or naming.
   - **Unknown**: cannot be determined from available evidence.
7. Read only the context needed to explain the target accurately. Do not load the entire repository without reason.
8. If tests contradict comments or naming, call out the discrepancy.
9. If multiple callers use the file differently, explain the distinct usage paths.
10. If the file is generated, vendored, or framework boilerplate, identify that early and adjust depth accordingly.

---

## Workflow

### Step 1 — Establish Repository Context

Inspect the target file and search for the smallest useful surrounding context.

Look for:

- imports and imported symbols,
- modules/packages containing the file,
- callers/importers,
- interfaces / protocols / abstract base classes,
- implementations,
- schemas / models / types,
- configuration,
- tests,
- README / ADR / design docs,
- related files with similar responsibility.

Do not start with a detailed explanation of the file body.

First answer internally:

- Which subsystem does this belong to?
- What responsibility does this file appear to own?
- What are the important upstream and downstream relationships?

If the role is still unclear, expand the search before explaining.

---

### Step 2 — Build the Mental Model First

Start with the system's job: what arrives, what processing happens, and what result
is consumed. Then explain the target file's contribution, who uses it, and who
consumes its output. Use a short paragraph rather than compressing these
relationships into a phrase such as "defines data contracts".

Before implementation details, provide an ASCII diagram suited to the file:

- For executable modules, show the relevant callers, processing, and consumers.
- For models, schemas, interfaces, or configuration, show which modules use the
  definitions. Do not portray a data type as an active processing step.

State what arrows mean: calls, data movement, or dependency. Label mixed edge
kinds explicitly, or use separate diagrams. Do not force every file into
`caller -> target -> downstream`; shared definitions can have several users.
If a relationship is uncertain, label it rather than inventing an edge.

Follow the diagram with one concrete walkthrough grounded in the repository.
Trace an input, operation, or configuration value through the relevant modules;
name the actor, representation, and transformation at each important transition.
Use a test fixture when suitable. Label constructed inputs as illustrative and
unexecuted examples as unexecuted; they are not evidence of a successful run.
For declarations without runtime behavior, show how a caller uses the definition.
Do not invent consumers when no caller can be found.

Only then expand the implementation details needed to understand that walkthrough.

---

### Step 3 — Explain the File by Logical Sections

Group the file into logical responsibilities instead of line ranges.

Typical sections:

- imports / dependencies,
- constants / configuration,
- data structures / types,
- public API,
- internal helpers,
- state management,
- error handling,
- side effects.

For each important section explain:

1. What does it do?
2. Why is it needed?
3. Who uses it?
4. What important assumption or invariant does it rely on?
5. What could break if it is changed incorrectly?

Skip trivial syntax unless it affects behavior.

---

### Step 4 — Trace Data Flow

Identify the important data entering and leaving the file.

For executable paths that transform data, trace the stages that actually occur:

`Input → Validation → Transformation → Decision → Side Effect → Output`

Explain:

- source of the input,
- important intermediate representations,
- validation / filtering / mapping,
- state mutations,
- persistence,
- network calls,
- caching,
- emitted events,
- final consumer of the output.

If useful, use a concrete simplified example.

---

### Step 5 — Trace Control Flow

Identify non-trivial execution paths:

- branches,
- early returns,
- loops,
- async/await,
- callbacks,
- retries,
- fallbacks,
- exception paths,
- feature flags.

For each significant branch, explain the trigger and consequence.

Do not enumerate branches that are syntactically present but unimportant to understanding the behavior.

---

### Step 6 — Repository Relationships

Search for the target file's most important relationships.

Prefer:

- direct callers/importers,
- direct dependencies,
- interfaces implemented,
- tests,
- config,
- schema/model definitions,
- sibling implementations.

Present only the relationships that materially improve comprehension.

Suggested format:

| Relationship | File/Symbol | Why it matters |
|---|---|---|
| Caller | `...` | initiates ... |
| Dependency | `...` | provides ... |
| Test | `...` | establishes ... |

---

### Step 7 — Read Tests as Contract Evidence

Inspect relevant tests when available.

Extract:

- happy paths,
- edge cases,
- invariants,
- failure behavior,
- mocking boundaries,
- expected side effects.

Answer:

> What contract do the tests imply for this file?

If no tests exist, state that explicitly.

Do not invent expected behavior merely because it would be conventional.

---

### Step 8 — Explain Non-Obvious Design Decisions

Identify code that may look unusual, indirect, repetitive, or over-engineered.

Before criticizing it, look for supporting evidence in:

- callers,
- tests,
- comments,
- configuration,
- interfaces,
- related implementations,
- version-control context if available.

Then classify the explanation as:

- **Confirmed**
- **Inferred**
- **Unknown**

Do not claim design intent unless evidence supports it.

---

### Step 9 — Surface Risks and Modification Boundaries

Identify the most important things a developer should know before editing this file.

Examples:

- ordering assumptions,
- idempotency requirements,
- concurrency constraints,
- serialization format,
- compatibility requirements,
- caching behavior,
- transaction boundaries,
- retry semantics,
- shared mutable state,
- externally visible contracts.

Only include risks grounded in repository evidence.

---

## Explanation Requirements

The workflow is an internal investigation checklist, not a mandatory numbered
report. Organize the answer around the reader's understanding; omit empty or
redundant sections and vary the depth by the file's responsibilities.

The opening must establish the system's job and the target file's role, followed
by the architecture/dependency diagram and concrete walkthrough from Step 2.
Then explain significant implementation behavior, tests, and modification
constraints. Keep supporting file/symbol references near the claims they support.

### Language and detail

- Match the user's language. Retain exact identifiers, paths, and field values.
- Explain abstract terms through concrete actors and behavior on first use.
  "Input compatibility" needs an explanation of which formats are accepted and
  how the caller obtains the data; the label alone is insufficient.
- For each important behavior, explain its trigger, actor, and consequence.
  "Processing success does not guarantee delivery" needs the actual delivery
  condition and the module that decides it.
- Prefer connected prose for causality and examples. Use tables for mappings or
  comparisons and lists for genuinely parallel items, not as sentence fragments.
- Do not shorten away the relationships that make a statement understandable.
  Remove repetition and unrelated detail before removing explanation.
- Do not list every symbol equally. Prioritize the behavior needed for orientation;
  explain unused declarations separately when they materially affect understanding.
- Keep Confirmed, Inferred, and Unknown distinguishable in context; separate
  headings are optional. Naming alone is not proof of design intent.
- Distinguish tests read from tests run. Report actual results only for commands
  executed, and state the limits of verification.

### Flexible output

Choose headings only when they help navigation. A useful answer usually includes:

- system context and file role,
- a labeled ASCII diagram and one walkthrough,
- important implementation behavior and repository relationships,
- test evidence, relevant modification constraints, and remaining uncertainty.

Do not reproduce twelve fixed sections or repeat the same diagram and explanation
under several headings. Include next-reading suggestions only when they identify
an unresolved relationship. Knowledge-check questions are optional unless asked
for; they must not replace missing explanation.

## Final Writing Pass — sepia

After repository investigation and drafting, use the available `sepia` skill to
review and revise the explanation. Read its SKILL.md and the references required
by its non-fiction routing; do not merely mention the skill or assume its rules.
This pass edits the explanation, not the repository.

Check structure before wording: can the reader identify the system's job, the
file's role, the diagram's edge meanings, and the walkthrough's actors? Diagnose
unclear abstractions, unexplained consequences, and repeated sections before
editing. Keep the defect list internal unless the user asks for an editing report.

Preserve the verified facts during revision: exact identifiers, paths, numbers,
field values, conditions, test results, and uncertainty labels. Do not invent
motives, simplify away branch conditions, or turn an inference into a fact.
After revision, compare changed claims and diagram relationships with the
repository evidence before returning the answer.

If `sepia` is unavailable, disclose the missing writing pass briefly and apply the
Explanation Requirements directly. Do not silently claim it ran, install a skill,
or block an otherwise supported file explanation.

## Examples

### Example 1 — A model definition file

Request: "Explain `app/models.py` in repository context."

Expected approach: explain the service's input and output before listing model
fields. Draw the verified modules that consume the model definitions, with edges
labeled "uses type". Walk a fixture through parsing, processing, and serialization
only when those relationships exist in the repository. Explain a validation or
compatibility rule through its effect on a caller. Do not place model class names
in an execution chain as if they were workers.

### Example 2 — A queue worker

Request: "Help me understand `app/worker.py`, especially retries."

Expected approach: establish what the worker receives and what finishes a job.
Draw calls and message movement with distinct labels. Walk one verified failure
path from receipt to retry or acknowledgement, explaining each decision's trigger
and consequence. Keep test mocks and unexecuted examples separate from evidence
of actual delivery. Let retry behavior take more space than imports or constants.

---

## Depth Modes

### quick

Use when the user needs orientation.

Inspect:

- target file,
- direct callers,
- direct dependencies,
- one or two relevant tests.

Keep the answer focused on orientation: system context, file role, a diagram,
a brief walkthrough, and only the most consequential constraints. Retain the
final writing pass; quick mode reduces investigation breadth, not clarity.

### standard

Use the full workflow.

### deep

Additionally inspect:

- all materially distinct callers,
- related implementations,
- broader tests,
- config,
- design docs / ADRs,
- version-control context if available.

Use deep mode only when the added context materially improves understanding.

---

## Stop Rule

Stop expanding repository context when all of the following are clear:

- the file's architectural role,
- its main caller(s),
- its critical dependencies,
- its core data/control flow,
- its externally observable behavior,
- and the important constraints established by tests or interfaces.

Do not keep searching merely because more files exist.
