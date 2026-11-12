# Codex catalog variants and no-account installation path

Date: 2026-11-11. Status: working-tree implementation and offline tests passed;
the later [native no-account capability case](codex-no-account-native-results.md)
also passed. The user selected official-route
support, then clarified that support means **installing Superpowers without a
coding-agent account login**, including colleagues using a company AI endpoint.
Endpoint configuration assistance is outside this change.

## Behavior

One Superpowers menu item follows exactly one official marketplace exposed by
native Codex: `openai-curated` reads `marketplace.json`; `openai-api-curated`
reads `api_marketplace.json`. Both names refer to OpenAI's official plugin
repository; native inventory determines the route. No endpoint URL, auth file,
account credential or model request is used to guess the name.

The effective name stays bound through the menu, dependency eligibility,
installation plan, pre-execution recheck, native selector and receipt checks.
An acceptance record for one catalog never authorizes the other. Two exposed
official catalogs, a wrong/missing selected manifest, source conflict, or a
catalog change after consent withholds installation. Existing Superpowers is
preserved, including disabled or newer installations. A missing catalog gives
native `/plugins` preparation guidance without demanding ChatGPT login.

Company model settings and authentication environment variables are retained;
the installer does not configure or test the endpoint. Model access and plugin
download access are independent. README instructions now make this explicit.
Provider schema 2 and its single primary descriptor per host remain; runtime
resolution changes the effective Codex name without duplicating the menu.

## VERIFIED

- Nine new synthetic tests passed. They cover selection of the API manifest
  even if the main manifest is malformed, exact catalog-specific acceptance,
  wrong/duplicate/missing entries, conflicting/ambiguous sources, synthetic
  company provider configuration and environment-secret preservation, absence
  of an auth file, successful simulated native install/receipt, a wrong-catalog
  receipt after a write, preserved disabled installations, and catalog changes
  after consent. Every inventory query is named; no login, App Server or model
  command is issued by these transcripts.
- Installer suite: `python3 -m unittest discover -s tests -p 'test_installer*.py'`:
  **96 tests, 95 passed, 1 PowerShell process test skipped**, exit 0.
- Package checks: 14 passed; agent-skills configuration checks: 15 passed;
  `validate_skills_catalog.py --check`: exit 0; Python AST and `git diff --check`
  passed.
- The first six feature tests failed against old code (3 assertion failures,
  3 validation errors). A corrected-path replay of all nine tests against the
  preserved old production modules failed eight (4 failures, 4 errors); the
  existing-install preservation test already passed. No product file was
  reverted to perform that replay.
- Compared to the preceding catalog-probe baseline, 48 protected hashes
  outside the four intentionally changed runtime modules match, as do four
  original personal settings fingerprints, HEAD, four stashes and staged list.
  Provider hashes remain unset, acceptance records remain empty, R5 is unchanged.
  This implementation turn ran no external/native installation or model call.

Local checker corrections are retained: an early synthetic fixture used macOS
`/var` instead of canonical `/private/var` and failed the existing receipt/root
checks; the fixture now resolves its temporary base. A first old-code replay
lacked the shared `agent_skills_runtime` import path and was not evidence; its
corrected replay above is evidence. The misspelled `test_config*.py` selection
ran zero tests (exit 5); the correct `test_agent_skills_config.py` ran 15 and
passed. None of these corrections repeated an external action.

Evidence: `.superpowers/sdd/2026-11-11-codex-api-adapter/` holds red/replay/full
suite outputs. Pre-edit runtime and fixture copies are retained under
`/var/folders/2s/9t8b0pnx55758v09qzkxpk500000gn/T/codex-api-catalog-before-2zci08gq/`.

## Same-session Codex review

No findings. Self-review in same Codex session: commitment / recency / framing
bias not fully controlled. Scope: changes to `providers.py`, `hosts.py`,
`planning.py`, `ui.py`, the synthetic CLI fixture and new catalog-variant tests;
adjacent receipt/catalog contracts and the three README updates were inspected.
No external reviewer or subagent was used.

Adversarial checks: ambiguity cannot select a preferred name; a prepared main
manifest cannot rescue a missing API manifest; main acceptance cannot enable
API installation; a route switch after consent prevents mutation; wrong native
receipt identity reports an uncertain write without retry or removal. No
additional issues found. Syntax checks passed; no syntax finding was inferred.

Assumptions and limits: native inventory must reflect effective policy; the
exact CLI 0.167.0 adapter is still the supported baseline. Synthetic configuration
preservation does not prove that a real company provider is usable. Exact
native installation, source policy and enablement must be tested separately.

## NOT VERIFIED

Installer end-to-end acceptance, actual company endpoint connectivity, Windows/
Linux, plugin execution/hooks/model behavior, and whole-computer side effects.
The native `--available` result was subsequently verified in the linked native
case. The full repository's
network-dependent build/release gates were not run. No new ZIP, acceptance
record, commit, push or release was created. R5 does not contain this adapter.

The [separately approved no-account native case](codex-no-account-native-results.md)
verified actual native installation after this offline change. It did not
enable the production acceptance gate or rebuild the ZIP.
