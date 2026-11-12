# Superpowers reference-source evidence proposal

Date: 2026-11-11. Status: **APPROVED; BOTH REFERENCE FETCHES COMPLETED ONCE**.
The user approved this scope with `ok`. See [findings](superpowers-reference-findings.md).
The retained scope below does not authorize another external operation.

## Purpose

Complete two missing pieces before changing the Superpowers installer path:

1. Independently verify the fixed upstream content corresponding to the
   preserved Claude 7.0.0 installation. Its observed installed hash alone is
   not an independent expected value.
2. Read the matching Codex 0.167.0 source to identify the actual native path for
   preparing the official catalog. Local saved schema/excerpts identify
   candidate interfaces but do not establish their initialization effects.

Retain the confirmed policies: official catalogs first, different host versions
allowed, existing providers preserved and only the current operation's Git to
archive transition in scope. This step does not reopen those choices.

## Exactly two proposed external fetches

Prepared root:
`.superpowers/sdd/2026-11-11-superpowers-evidence/prepared-_zbibmjg/`.

Two empty independent bare Git repositories have been initialized there. They
are reference repositories, not native marketplace or plugin-cache state.
The exact absolute paths/environment are recorded in `run.json`. With
`<root>` substituted for the prepared directory, the complete external budget is:

```text
git -C <root>/superpowers.git fetch --no-tags --depth=1 https://github.com/obra/superpowers.git bb92a77741419a4ab5f06e711a283343f1ada0c3
git -C <root>/codex.git fetch --no-tags --depth=1 https://github.com/openai/codex refs/tags/rust-v0.167.0
```

Each fetch is allowed once, without retry or fallback to a mutable main branch.
The helper refuses unapproved execution and consumes a one-use marker before
each fetch. A missing ref, timeout or nonzero exit leaves the partial reference
state for inspection; it does not trigger another fetch.

## Effects and boundaries

These commands download public source objects from GitHub and write Git objects,
fetch metadata and local evidence under the new prepared directory. They do not
install a plugin, start a model/App Server session, authorize hooks, copy
credentials or change Claude/Codex settings. No model token charge is planned.
The Codex source download can be larger than the installer archive; no exact
download size is claimed before fetch.

Use an explicit clean environment and separate HOME/TMPDIR. Git reads no
global/system configuration and cannot prompt for credentials. No downloaded
script, hook, build, dependency installer or test suite is executed. Local Git
object reads and Python standard-library comparisons are included.

Preserve R5, all earlier packages/evidence, original native directories, stashes
and product code. No acceptance record or expected payload hash is written to
the product, and no commit/push/cleanup is included.

## Local work after the approved fetches

For Superpowers, require the fetched commit to equal the complete fixed SHA.
Enumerate committed paths, file modes and blob contents from Git objects, then
compare every path/byte fingerprint to the preserved native installation and
its 238-file observation. Keep mismatches explicit; do not add an arbitrary
ignore list, normalize content or substitute the observed hash for a proof.
Any source-control/bookkeeping exclusion needs an explicit content contract.

For Codex, retain the fetched tag's actual commit. Inspect the CLI, plugin
manager/curated loader, TUI `/plugins` and App Server handlers as needed, locally
from that source. Produce a concrete native initialization candidate with its
request/command vectors, authentication/model requirements and expected writes,
or identify the remaining unknown precisely. A schema field is not proof that
an operation is side-effect free or initializes the catalog.

The resulting evidence will determine the smallest correction and next native
test scope. Downloading these references does not approve implementation or a
new native installation.

## VERIFIED / NOT VERIFIED at preparation

VERIFIED: local target configuration still has unknown Superpowers payload
hashes and an empty acceptance index; Claude still requires Git metadata in
its provider adapter; saved Codex protocol/excerpts do not prove initialization.
The preparation created only empty reference repositories and an approval-
guarded helper. No fetch ran.

NOT VERIFIED: independent fixed-tree agreement; current official catalog state;
Codex initialization behavior; Claude archive provenance/transition trigger;
new installer behavior or native/model acceptance. Context7 is not exposed in
this session; no external documentation lookup was silently substituted.
