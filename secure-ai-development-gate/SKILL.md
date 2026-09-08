---
name: secure-ai-development-gate
description: Use when AI-assisted work may involve secrets, customer data, sensitive internal information, risky AI-generated output, or repository commits — inspect prompts, files, screenshots, logs, source code, and staged changes rather than trusting repository classification; sanitize sensitive data before AI processing, review AI output, preserve normal engineering checks, and block unsafe commits.
license: Proprietary
compatibility: >
  Designed for coding agents with repository/file access. Git and an available
  secret scanner are recommended but not required. If a required check cannot
  be performed, report it explicitly rather than claiming it passed.
metadata:
  version: "1.0"
  category: "security"
---

# Secure AI Development Gate

## Purpose

Prevent secrets, customer data, sensitive internal information, unsafe
AI-generated output, and unresolved license risks from entering:

1. AI prompts or AI context,
2. AI-assisted implementation workflows, or
3. company repositories.

This skill is a safety gate around AI-assisted development.

It does **not** replace:

- code review,
- testing,
- security scanning,
- license review,
- privacy requirements,
- company policy,
- or other required engineering controls.

---

# When to Use This Skill

Load and apply this skill when any of the following is true:

- repository source code may contain secrets or sensitive data before AI use;
- files will be attached or read into AI context and may contain sensitive data;
- screenshots will be analyzed and may expose customer/internal data;
- logs, stack traces, crash dumps, or terminal output may contain credentials or customer data;
- configuration files or environment data are involved;
- support cases or customer data are involved;
- business-operation data is involved;
- sensitive internal information may be present;
- AI-generated output is security-sensitive, privacy-sensitive, or license-sensitive;
- repository changes are about to be committed;
- the user asks whether content is safe to send to AI;
- the user asks for secret detection, sanitization, or data redaction.

Do not load this skill merely because a task involves ordinary low-risk coding.

Do not rely solely on repository classification to decide whether this skill applies.

---

# Core Workflow

Use this sequence:

```text
CLASSIFY TASK
    ↓
INSPECT INPUT
    ↓
DETECT SECRETS / SENSITIVE DATA
    ↓
SANITIZE OR MINIMIZE IF REQUIRED
    ↓
RECHECK SANITIZED INPUT
    ↓
PERFORM AI-ASSISTED TASK
    ↓
REVIEW GENERATED OUTPUT
    ↓
RUN NORMAL DEVELOPMENT CHECKS
    ↓
INSPECT STAGED CHANGES
    ↓
COMMIT GATE
```

The gates are independent.

Passing one gate does not imply that another gate passed.

---

# Gate 0 — Determine the Exposure Surface

Before performing the task, determine what information may enter AI context.

Inspect the **actual task**, not just the repository.

Consider:

- user prompt,
- repository files,
- source code,
- configuration files,
- environment files,
- attached files,
- screenshots,
- images,
- logs,
- stack traces,
- crash reports,
- terminal output,
- clipboard content,
- API requests and responses,
- support cases,
- tickets,
- database records,
- generated artifacts,
- staged Git changes.

A repository marked internal, private, public, or AI-approved may still
contain data that must not be sent to AI.

Repository classification is one input to the decision, not the decision.

---

# Gate 1 — Secret Detection

## Requirement

Inspect relevant repository content and task inputs for potential secrets
before exposing them to AI.

When practical, also perform a repository-level secret scan to detect
credentials that may exist outside the immediately requested files.

Look for:

- API keys,
- access tokens,
- refresh tokens,
- OAuth credentials,
- passwords,
- private keys,
- signing keys,
- encryption keys,
- service-account credentials,
- database credentials,
- cloud credentials,
- webhook secrets,
- session cookies,
- authentication cookies,
- Authorization headers,
- Bearer tokens,
- connection strings,
- credentials embedded in URLs,
- `.env` values,
- CI/CD secrets,
- registry tokens,
- certificates containing private material,
- high-entropy credential-like strings.

Do not assume that a value is safe because it is:

- in a test file,
- commented out,
- expired,
- labeled as an example,
- partially masked,
- inside a private repository,
- or already present in Git history.

When uncertain whether a value is a real secret:

```text
Treat it as sensitive until verified otherwise.
```

---

## Secret Scan Execution

When this skill is active and repository/file access is available, do not rely
only on visual inspection.

For repository or file-level exposure, run:

```bash
scripts/scan-secrets.sh <target>
```

before exposing the relevant content to AI when practical.

Before committing staged changes, run:

```bash
scripts/scan-staged-secrets.sh
```

Interpret exit codes as:

```text
0 → PASS
2 → BLOCKED / NEEDS_REVIEW
3 → SCAN ERROR / NOT VERIFIED
```

An exit code of `3` must never be interpreted as a successful scan.

Use available company-approved secret scanning tools first.

Examples:

```bash
gitleaks
trufflehog
detect-secrets
```

These are examples, not mandatory dependencies.

If these scripts are unavailable, use the strongest approved scanner available
in the environment.

If no scanner is available, perform fallback inspection and explicitly report:

```text
Secret detection: NOT FULLY VERIFIED
```

Never claim:

```text
No secrets detected.
```

if the relevant scan or inspection was not actually performed.

---

## Reporting Secrets

Do not repeat a detected secret in full.

Prefer:

```text
Possible API token detected:
sk-****7Qp2
```

Never unnecessarily print the original credential.

---

# Gate 2 — Sensitive Data Detection

Determine whether the task contains:

## Customer or personal data

Examples include:

- names,
- email addresses,
- phone numbers,
- physical addresses,
- account identifiers,
- customer IDs,
- user IDs,
- device identifiers,
- identifiable IP addresses,
- transaction records,
- support tickets,
- customer communications,
- telemetry tied to identifiable users,
- screenshots containing customer information.

## Sensitive internal information

Examples include:

- unreleased product information,
- confidential product plans,
- internal architecture,
- internal incident information,
- vulnerability information,
- private endpoints,
- internal hostnames,
- proprietary datasets,
- confidential business metrics,
- partner-confidential information,
- confidential internal documents,
- credentials or authentication material.

The list is illustrative, not exhaustive.

Consider both explicit identifiers and information that becomes sensitive when
combined with other fields.

---

# Gate 3 — Mandatory Sanitization for Customer Data

For work involving customer data, including support cases and business
operations, enforce a two-stage workflow.

## Stage 1 — Pseudonymization and Data Sanitization

Before AI-assisted analysis, development, or execution:

1. remove fields unnecessary for the task;
2. redact confidential content;
3. replace identifiers with synthetic identifiers;
4. mask credentials and secrets;
5. generalize exact values when precision is unnecessary;
6. preserve only relationships required for analysis.

Example:

```text
BEFORE

Customer: alice@example.com
Account ID: 827461992
Phone: +886-912-345-678
IP: 203.0.113.24
Access Token: eyJhbGciOi...

AFTER

Customer: USER_001
Account ID: ACCOUNT_001
Phone: PHONE_001
IP: CLIENT_IP_001
Access Token: [REDACTED]
```

Preserve referential consistency.

If two events belong to the same customer:

```text
USER_001
```

must continue to identify the same pseudonymous entity within the sanitized
dataset.

Do not replace the same customer with unrelated identifiers across records if
doing so would break the required analysis.

---

## Stage 2 — AI-Assisted Implementation

Only use the sanitized representation for subsequent:

- analysis,
- debugging,
- coding,
- scripting,
- automation,
- report generation,
- investigation,
- pattern detection,
- implementation,
- execution.

The flow is:

```text
ORIGINAL DATA
    ↓
SANITIZE
    ↓
VERIFY SANITIZATION
    ↓
SANITIZED DATA
    ↓
AI-ASSISTED WORK
```

Do not use:

```text
ORIGINAL CUSTOMER DATA
    ↓
AI-ASSISTED WORK
    ↓
SANITIZE OUTPUT
```

Sanitization must happen **before** AI-assisted processing.

---

# Gate 4 — Data Minimization

Even when information is permitted, use the minimum necessary data.

Prefer:

```text
minimum necessary context
```

over:

```text
all available context
```

Examples:

Do not provide an entire repository when five files are sufficient.

Do not provide a complete production log when twenty relevant lines reproduce
the issue.

Do not provide a full customer profile when two sanitized fields are
sufficient.

Do not provide production data when synthetic data reproduces the behavior.

Do not provide an entire configuration file when one sanitized section is
sufficient.

---

# Gate 5 — Recheck Before AI Use

After sanitization or minimization, inspect the resulting content again.

Confirm:

```text
[ ] No known secret remains
[ ] Customer identifiers are removed or pseudonymized
[ ] Confidential content not required by the task is removed
[ ] Data has been minimized
[ ] Referential relationships required by the task are preserved
[ ] Sanitization did not expose sensitive values indirectly
```

Only then continue with AI-assisted work.

---

# Gate 6 — Review AI-Generated Output

Treat AI-generated output as:

```text
UNVERIFIED INPUT
```

not:

```text
TRUSTED OUTPUT
```

This applies to:

- source code,
- scripts,
- shell commands,
- configuration,
- infrastructure definitions,
- tests,
- documentation,
- technical analysis,
- architecture recommendations,
- security recommendations,
- dependency recommendations,
- migration instructions,
- generated data.

Review the output before using it.

## Correctness Review

Check applicable areas including:

- logic,
- functional correctness,
- edge cases,
- error handling,
- assumptions,
- compatibility,
- existing repository conventions,
- failure behavior.

Verify important assumptions against evidence whenever practical.

## Security Review

Check applicable areas including:

- authentication,
- authorization,
- input validation,
- injection,
- command execution,
- unsafe file operations,
- path traversal,
- insecure deserialization,
- cryptography,
- secret exposure,
- logging,
- privilege boundaries,
- dependency security,
- unsafe defaults,
- XSS from generated web content (escape untrusted output before embedding it in HTML, templates, or markup),
- injection through generated shell or SQL (validate parameters against allowlists, never interpolate raw input).

## License Review

Check whether generated code or suggested dependencies introduce:

- copied third-party implementation,
- incompatible licenses,
- dependencies with unacceptable licenses,
- unattributed copied material,
- suspiciously recognizable third-party code,
- code whose provenance or license risk cannot reasonably be resolved.

AI-generated code is not automatically license-safe.

If license risk remains unclear:

```text
BLOCK COMMIT
```

until the issue is resolved.

## Company Policy Review

Apply applicable company requirements concerning:

- AI usage,
- privacy,
- security,
- data handling,
- source code,
- architecture,
- approved dependencies,
- development standards,
- legal and compliance requirements.

Do not infer company approval merely because the agent can technically perform
an operation.

---

# Gate 7 — Normal Development Validation

AI assistance does not reduce normal engineering requirements.

Run applicable existing project checks, including:

- code review,
- unit tests,
- integration tests,
- regression tests,
- linting,
- type checking,
- static analysis,
- build validation,
- dependency scanning,
- vulnerability scanning,
- secret scanning,
- license scanning,
- security review,
- CI checks.

Use the repository's established validation workflow whenever available.

Do not invent substitute checks when the repository already defines the
required commands.

Do not bypass required checks because:

```text
The AI reviewed the code.
```

---

# Gate 8 — Commit Safety Gate

Before committing changes to a company repository, inspect what will actually
be committed.

At minimum, when Git is available, inspect:

```bash
git status
git diff --cached
```

When useful, also inspect:

```bash
git diff
```

Check staged content for:

- secrets,
- credentials,
- customer data,
- production data,
- confidential information,
- generated temporary artifacts,
- debug logs,
- AI-generated code with unresolved license risk.

Run:

```bash
scripts/scan-staged-secrets.sh
```

before commit when the script is available.

A successful automated secret scan does not replace staged-diff inspection.

---

## Error Handling

**Scanner failure modes and required responses:**

- `scan-secrets.sh` exits `0` (pass), `2` (finding — BLOCKED / NEEDS_REVIEW),
  or `3` (scan error). Exit `3` means the scan did not run to completion;
  report `Secret detection: NOT FULLY VERIFIED` and never treat it as a pass.
- `scan-staged-secrets.sh` exits `3` when the current directory is not a Git
  working tree, when the gitleaks staged scan fails, or when the fallback scan
  itself errors. An empty staged diff exits `0` with no scan. Respond as
  above; do not commit until a completed scan or a manual staged-diff
  inspection exists.
- Missing `gitleaks` and `trufflehog`: both scripts fall back to a shared
  fixed pattern list (single-line ERE compatible with `rg` and `grep -E`).
  State that the fallback scanner was used; it detects less than dedicated
  tools and produces false positives on ordinary assignments.
- `mktemp` failure: the script aborts under `set -e` with mktemp's own exit
  status. Treat any unexpected nonzero exit as NOT VERIFIED.
- Scanner timeout or truncated output: treat as the exit `3` case —
  NOT VERIFIED, not a pass.

**Gate behavior on script error:** an incomplete scan provides no evidence.
Apply the Tool Evidence Rule — report `NOT VERIFIED`, fall back to manual
staged-diff inspection, and do not claim the commit gate passed.

---

# Hard Block Conditions

Use:

```text
BLOCKED
```

when any of the following applies.

## Secret detected

Do not send the secret to another AI system.

Do not commit it.

Mask it when reporting.

Recommend rotation when the credential reached any system outside the local
machine (sent to another AI system, committed, pushed, logged, or shared),
or when exposure cannot be ruled out.

## Unsanitized customer data detected

Do not proceed directly to AI-assisted implementation.

Sanitize first.

## Sensitive data cannot be safely sanitized

Stop before exposing the original data.

Report:

- what information appears necessary,
- why sanitization would prevent the task,
- what additional approved handling would be required.

Do not silently proceed.

## Unresolved license risk

Do not commit affected generated code.

Identify the uncertain code, dependency, or provenance issue.

## Required validation failed

Do not claim the change is ready.

## Required validation could not be performed

Do not claim the check passed.

Report it as:

```text
NOT VERIFIED
```

---

# Tool Evidence Rule

A safety check is considered completed only when there is evidence that the
corresponding inspection, command, test, or scanner was actually executed.

The agent MUST NOT convert:

```text
I should check...
```

into:

```text
Checked.
```

without execution evidence.

Examples of acceptable evidence:

- scanner command executed,
- files inspected,
- staged diff inspected,
- test command executed,
- CI result observed,
- license metadata inspected.

If execution is unavailable, report:

```text
NOT VERIFIED
```

instead of:

```text
PASS
```

---

# Prompt Safety Check

Before exposing task material to AI, evaluate:

```text
[ ] Prompt inspected
[ ] Relevant source files inspected
[ ] Attached files inspected
[ ] Screenshots inspected
[ ] Logs / terminal output inspected
[ ] Secrets considered
[ ] Customer data considered
[ ] Sensitive internal data considered
[ ] Data minimized
[ ] Required sanitization completed
[ ] Sanitized data rechecked
```

Evaluate only items applicable to the task.

Do not mark an unperformed check as complete.

---

# Output Safety Check

Before applying, executing, publishing, or committing AI-generated output:

```text
[ ] Technical correctness reviewed
[ ] Important assumptions verified
[ ] Security implications reviewed
[ ] Secrets absent
[ ] Customer data absent or appropriately sanitized
[ ] License risk reviewed
[ ] Company-policy requirements considered
[ ] Required tests performed
[ ] Required security checks performed
[ ] Required code review preserved
```

---

# Decision Model

Use the following decision rules:

```text
SECRET
→ BLOCK

CUSTOMER DATA
→ SANITIZE
→ RECHECK
→ CONTINUE

SENSITIVE INTERNAL DATA
→ MINIMIZE / SANITIZE
→ RECHECK
→ CONTINUE ONLY IF PERMITTED

NORMAL SOURCE CODE
→ SECRET CHECK WHEN EXPOSURE RISK EXISTS
→ MINIMIZE CONTEXT
→ CONTINUE

AI-GENERATED SECURITY / PRIVACY / LICENSE-SENSITIVE OUTPUT
→ REVIEW
→ TEST
→ SECURITY CHECK
→ LICENSE CHECK
→ CONTINUE

UNCLEAR LICENSE RISK
→ BLOCK COMMIT

FAILED REQUIRED VALIDATION
→ NOT READY

CHECK NOT PERFORMED
→ NOT VERIFIED

ALL APPLICABLE GATES PASS
→ SAFE TO CONTINUE
```

---

# Agent Behavior

## The agent MUST

- inspect actual task content instead of relying solely on repository
  classification;
- consider prompt text, files, screenshots, logs, and generated output as
  potential exposure surfaces;
- inspect relevant repository content for secrets when exposure risk exists;
- sanitize customer data before AI-assisted processing;
- minimize unnecessary data;
- preserve useful relationships when pseudonymizing data;
- recheck sanitized content;
- review risky AI-generated output;
- evaluate correctness, security, license risk, and applicable company policy;
- preserve normal engineering validation;
- inspect staged changes before commit;
- clearly distinguish checks performed from checks not performed;
- block unsafe commits;
- mask secrets when reporting them.

## The agent MUST NOT

- assume a private repository is safe;
- assume repository classification is sufficient;
- assume test data is non-sensitive;
- unnecessarily reproduce detected secrets;
- send unsanitized customer data because the task is urgent;
- sanitize customer data only after AI processing;
- treat AI-generated output as trusted;
- replace testing or code review with AI review;
- claim a security or license check passed when it was not performed;
- commit secrets;
- commit customer data that should not be stored in the repository;
- commit AI-generated code with unresolved license risk.

---

# Reporting

Do not produce a large security report when there are no findings.

For normal successful execution, keep the safety report concise.

Use:

```text
Security gate: PASS

- Secret exposure: no known issue detected
- Sensitive data: none detected / sanitized
- AI output review: completed
- Required development checks: <performed checks>
- Commit gate: passed / not applicable
```

When a problem is found, use:

```text
Security gate: BLOCKED | NEEDS_REVIEW

Finding:
<what was detected>

Location:
<file, input, attachment, log, screenshot, generated output, or staged diff>

Risk:
<why the issue matters>

Action:
<required sanitization, removal, verification, rotation, or review>

Verification:
<what was actually checked and what remains unverified>
```

Never include a complete detected secret in the report.

---

# Usage Examples

## Example 1 — Commit gate blocks customer data in staged changes

Scenario: an agent-assisted fix touches a configuration file, and the staged
diff includes `customer_email=alice@example.com` copied from a support ticket.

Gates applied:

1. Gate 0 / Gate 2: the staged diff is an exposure surface, and the address is
   customer data.
2. Gate 8: run `scripts/scan-staged-secrets.sh`, then inspect
   `git diff --cached` — the scan alone does not replace inspection.
3. Finding: customer identifier inside a staged addition.

Outcome: unstage the line, replace the value with a synthetic placeholder,
re-run the scan, then commit. Report the finding with the value masked
(`alice@****.com`).

## Example 2 — Support-case log pasted for debugging

Scenario: the user pastes a stack trace from a support case to diagnose a
failure. The log contains `Authorization: Bearer eyJhbGciOi...` and a customer
account number.

Gates applied:

1. Gate 1: Bearer tokens are secrets; account numbers are customer data.
2. Gate 3: sanitize before AI-assisted analysis — replace the token with
   `[REDACTED]` and the account number with `ACCOUNT_001`, preserving request
   ordering so the trace stays analyzable.
3. Gate 5: recheck the sanitized log; no credential remains.

Outcome: analysis proceeds on the sanitized text. The original log is never
sent to AI context, echoed into reports, or committed.

---

# Execution Principle

Perform safety checks proportionally to the task.

Do not turn a trivial coding operation into an unnecessary full security audit.

At the same time, never skip a required gate merely to reduce effort.

The goal is:

```text
Inspect what crosses the AI boundary.
Sanitize sensitive data before it crosses that boundary.
Verify what AI produces before trusting it.
Inspect what crosses the repository boundary before committing it.
```

Final sequence:

```text
INSPECT
→ DETECT
→ SANITIZE
→ MINIMIZE
→ RECHECK
→ EXECUTE
→ REVIEW
→ TEST
→ SCAN
→ COMMIT
```
