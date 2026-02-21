---
name: micro-poc-validator
description: >-
  Empirically validate technical assumptions through minimal code experiments
  (5-30 min spikes). Use when a tech-feasibility assessment or design document
  contains claims that can be proven or disproven by running actual code.
  Triggered by "validate this assumption", "can X actually do Y?",
  "prove it with code", or "micro-poc".
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, WebSearch, WebFetch, Task, mcp__context7__resolve-library-id, mcp__context7__query-docs
---

# Micro-PoC Validator

## Overview

A hands-on validation skill that resolves technical uncertainties through
minimal executable experiments instead of desk research alone. Each
experiment is time-boxed, produces a binary outcome (PASS/FAIL/PARTIAL),
and records raw evidence (code + output) for traceability.

**Core principle:** If a claim can be tested in 30 minutes or less, test
it. A 10-line script that fails is worth more than 10 pages of theoretical
analysis that assumes success.

**Announce at start:**
> "Starting micro-PoC validation — I'll write minimal code to empirically
> test this assumption."

## When to Use

- A `tech-feasibility` report contains `?` (uncertain) items in its fit
  analysis
- A design document makes a technical claim that hasn't been verified by
  running code (e.g., "library X supports feature Y")
- Before committing to an architecture that depends on an unverified
  capability
- When desk research yields conflicting information and only an experiment
  can resolve it
- When a `critical-research` report labels a claim as "Uncertain"

**When NOT to use:**
- The claim is already verified by existing tests in the codebase
- The experiment would require > 30 minutes of setup (that's a real PoC,
  not a micro-PoC)
- The claim is about performance at scale (use benchmarks, not micro-PoCs)
- The answer is clearly documented in official docs with code examples

## Required Input

Collect before starting. If the user hasn't provided these, ask.

```
ASSUMPTION:   The specific technical claim to validate
               (e.g., "nodriver can connect to wss:// URLs")
CONTEXT:      Why this matters — what breaks if the assumption is wrong?
TIME_BOX:     Maximum time to spend (default: 15 minutes)
KILL_IMPACT:  What happens if validation FAILS?
               - BLOCKING: Entire approach is unviable → must pivot
               - DEGRADING: Approach works but with reduced capability
               - MINOR: Workaround exists → document and move on
```

## Workflow

### Step 1: Decompose Assumption into Testable Assertion

Rewrite the assumption as a concrete, binary assertion that code can
prove or disprove.

**Pattern:** "[Library/Tool] can [specific action] when [specific condition]"

| Vague assumption | Testable assertion |
|-----------------|-------------------|
| "nodriver supports remote browsers" | "nodriver.start(browser_ws_endpoint='wss://...') connects without error" |
| "ScraperAPI returns review data" | "GET /structured/amazon/product returns a `reviews` array with > 0 items for ASIN B075CYMYK6" |
| "Playwright can inject cookies via CDP" | "After browser.contexts[0].add_cookies([...]), Amazon.com shows logged-in state" |

**If the assumption decomposes into 2+ independent assertions, create
separate micro-PoCs for each.** Do not bundle unrelated tests.

### Step 2: Design Minimal Experiment

Write the smallest possible script that tests the assertion. Constraints:

- **Max 30 lines of code** (excluding imports and setup)
- **No production code changes** — standalone script only
- **No new dependencies unless testing that specific dependency**
  (e.g., if testing Playwright, installing it is allowed)
- **Deterministic** — avoid tests that depend on network timing or
  external state that might change between runs
- **Clear success/failure output** — print "PASS" or "FAIL" with
  evidence

**Experiment template:**

```python
#!/usr/bin/env python3
"""
Micro-PoC: [Assumption being tested]
Expected: [What should happen if assumption is true]
Time box: [N] minutes
"""
import sys

def test_assumption():
    try:
        # --- Setup (minimal) ---
        # [setup code]

        # --- Test ---
        # [the actual test, as few lines as possible]
        result = ...

        # --- Assert ---
        if [success_condition]:
            print(f"PASS: [evidence of success]")
            print(f"  Result: {result}")
            return True
        else:
            print(f"FAIL: [evidence of failure]")
            print(f"  Expected: [what was expected]")
            print(f"  Got: {result}")
            return False

    except Exception as e:
        print(f"FAIL: Exception — {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    success = test_assumption()
    sys.exit(0 if success else 1)
```

### Step 3: Pre-Flight Check

Before running the experiment, verify:

1. **Safety**: Does the script make external API calls that cost money?
   If yes, warn the user and confirm.
2. **Isolation**: Does the script modify any project files or state?
   If yes, use a temporary directory.
3. **Dependencies**: Does the script require installing packages?
   If yes, use a virtual environment or confirm with user.
4. **Credentials**: Does the script need API keys or auth tokens?
   If yes, check if they exist in the environment — never hardcode.

Present the experiment design to the user:

```
Micro-PoC Plan:
  Assumption:  [the claim]
  Test script: [brief description of what the code does]
  Dependencies: [any packages to install, or "none"]
  API calls:   [yes/no — if yes, estimated cost]
  Time box:    [N minutes]
  Risk:        [none / low / medium]

Proceed? [Y/n]
```

### Step 4: Execute Experiment

Run the script and capture all output. Record:

- **Exit code** (0 = pass, non-zero = fail)
- **stdout/stderr** (raw, unedited)
- **Execution time**
- **Any error messages or stack traces**

If the experiment hangs or exceeds the time box, kill it and record
"TIMEOUT" as the result.

### Step 5: Analyze and Record Result

Classify the outcome:

| Result | Meaning | Action |
|--------|---------|--------|
| **PASS** | Assumption confirmed empirically | Record as VERIFIED, proceed with design |
| **FAIL** | Assumption disproven empirically | Record as FALSIFIED, trigger pivot discussion |
| **PARTIAL** | Works under some conditions but not all | Record conditions, reassess design scope |
| **TIMEOUT** | Could not complete within time box | Escalate to full PoC or abandon |
| **BLOCKED** | Cannot test due to missing credentials/infra | Record blocker, suggest alternative test |

### Step 6: Generate Validation Report

```markdown
# Micro-PoC Report: [Assumption]

**Date**: YYYY-MM-DD
**Time box**: [N] minutes (actual: [M] minutes)
**Kill impact**: BLOCKING / DEGRADING / MINOR

## Assertion
[The specific testable claim]

## Experiment
```python
[The complete test script]
```

## Raw Output
```
[stdout + stderr, unedited]
```

## Result: PASS / FAIL / PARTIAL / TIMEOUT / BLOCKED

**Evidence**: [1-2 sentence summary of what the output proves]

## Implications
- [What this means for the design/plan]
- [If FAIL: what pivot options exist]
- [If PARTIAL: what conditions must be met]

## Source Verification
- [Official doc link that confirms or contradicts the finding]
- [GitHub issue/PR if relevant]
```

### Step 7: Update Upstream Documents (If Applicable)

If this micro-PoC was triggered by a `tech-feasibility` or design
document, suggest specific updates to that document:

- Change hypothesis status (Uncertain → Supported/Falsified)
- Update fit analysis (`?` → `Y` or `N`)
- Flag any cascading impacts on dependent assumptions

**Do NOT edit upstream documents automatically.** Present the suggested
changes and let the user decide.

## Batch Mode

When validating multiple assumptions from the same document:

1. List all assumptions with their KILL_IMPACT
2. Sort by KILL_IMPACT (BLOCKING first, then DEGRADING, then MINOR)
3. Execute sequentially — **stop on the first BLOCKING FAIL**
4. Generate a consolidated report

```markdown
# Micro-PoC Batch Report: [Document Name]

| # | Assumption | Kill Impact | Result | Time |
|---|-----------|-------------|--------|------|
| 1 | [claim]   | BLOCKING    | PASS   | 3m   |
| 2 | [claim]   | BLOCKING    | FAIL   | 5m   |

⚠️ Stopped at #2: BLOCKING assumption falsified.
Assumptions #3-#5 not tested.

## Recommendation
[Based on the FAIL, what should change in the design?]
```

## Examples

### Example 1: Library Capability Check

```
User: "Our design assumes nodriver can connect to wss:// URLs for remote
browser control. Validate this."

ASSUMPTION: nodriver.start() accepts a browser_ws_endpoint parameter for
            connecting to remote browsers via WebSocket
CONTEXT:    Tier 3 of our architecture requires connecting to ZenRows/
            Bright Data remote browsers via WSS
TIME_BOX:   10 minutes
KILL_IMPACT: BLOCKING — if nodriver can't connect to WSS, we must switch
             to Playwright

→ Step 1: Assertion = "nodriver.start(browser_ws_endpoint='wss://...') is
          a valid call signature"
→ Step 2: Script inspects nodriver's start() function signature and source
          code, attempts the call
→ Step 3: No API calls needed, no cost, safe
→ Step 4: Run script
→ Step 5: FAIL — nodriver.start() has no browser_ws_endpoint parameter.
          Source code confirms it only accepts host/port for local Chrome.
→ Step 6: Report with evidence
→ Step 7: Suggest updating tech-feasibility H1 from "Uncertain" to
          "Falsified", recommend Playwright as alternative
```

### Example 2: API Endpoint Validation

```
User: "Does ScraperAPI's Amazon Reviews endpoint still work?"

ASSUMPTION: GET https://api.scraperapi.com/structured/amazon/review/{asin}
            returns review data
CONTEXT:    Tier 2 depends on this endpoint for structured reviews
TIME_BOX:   5 minutes
KILL_IMPACT: DEGRADING — can fall back to raw HTML parsing

→ Step 1: Assertion = "API returns HTTP 200 with reviews array"
→ Step 2: 5-line curl/httpx script with API key
→ Step 3: Requires API key (check env), costs ~1 API credit
→ Step 4: Run script
→ Step 5: FAIL — Returns 404 or empty reviews array
→ Step 6: Report with raw HTTP response
→ Step 7: Suggest updating design to use raw HTML endpoint
```

### Example 3: Source Code Verification (No Execution)

```
User: "Can Playwright connect over CDP with connect_over_cdp()?"

ASSUMPTION: playwright.chromium.connect_over_cdp(wss_url) exists and
            accepts a wss:// URL
TIME_BOX:   5 minutes
KILL_IMPACT: BLOCKING

→ Step 1: Assertion = "connect_over_cdp method exists in Playwright's API"
→ Step 2: Script checks Playwright's installed source or uses Context7
          to query official docs
→ Step 3: No external calls, safe
→ Step 4: Query docs + inspect installed module
→ Step 5: PASS — Method exists, documented with wss:// examples
→ Step 6: Report with doc reference
```

## Constraints

- **Time box is sacred** — never exceed it. If the experiment needs more
  time, that's a signal it belongs in a full PoC, not a micro-PoC.
- **One assumption per experiment** — no bundling. Each micro-PoC tests
  exactly one thing.
- **Raw output preserved** — never edit, summarize, or "clean up" the
  actual output. Include it verbatim.
- **No production code changes** — experiments live in temporary
  files/directories and are cleaned up after.
- **BLOCKING FAILs halt the batch** — don't waste time testing downstream
  assumptions when a fundamental one has failed.
- **User approval before execution** — always present the experiment
  plan before running code, especially if it involves network calls or
  package installation.

## Error Handling

| Scenario | Action |
|----------|--------|
| Experiment requires credentials not in env | Record as BLOCKED, list what's needed |
| Package installation fails | Try alternative installation method once; if still fails, record as BLOCKED |
| Experiment produces ambiguous results | Record as PARTIAL, describe what worked and what didn't |
| Network timeout during API test | Retry once; if still fails, record as TIMEOUT with network conditions |
| Script has a bug (not the assumption) | Fix and re-run — don't count buggy scripts as assumption failures |
| User declines to run experiment | Record as SKIPPED with reason, flag remaining uncertainty |

## Security Considerations

- **Never hardcode credentials** — use environment variables only
- **Never run experiments that modify production data** — read-only tests
  only, or use sandboxed environments
- **Sanitize API responses** — strip any PII or sensitive data before
  including in reports
- **Temporary files only** — write experiment scripts to `/tmp` or a
  temporary directory, clean up after
- **Cost awareness** — always estimate and disclose API costs before
  making external calls
- **No blind execution** — always show the user the script before running

## Related Skills

- **tech-feasibility** — upstream: produces `?` items that become
  micro-PoC candidates
- **critical-research** — parallel: provides desk research evidence;
  micro-PoC provides empirical evidence
- **research-synthesis** — downstream: combines desk research + empirical
  results into decisions
- **brainstorming** — upstream: design choices may generate assumptions
  that need validation
- **tech-research-pipeline** — orchestrator: invokes this skill at the
  right phase in the research workflow
