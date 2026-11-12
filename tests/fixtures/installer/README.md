# Installer fixtures

Fixtures named `observed-*` are minimized/anonymized native output, with
`host`, `cli_version`, `platform`, `architecture`, `command`, `provenance`.
Placeholders such as `<SOURCE_ROOT>` replace private absolute paths.
They prove field shape only, not remote installation or functional acceptance.
Fixtures named `synthetic-*` are controlled examples, never native evidence.

Official-source test cases use `tests/installer_provider_fixtures.py` and temporary
catalog/payload/cache trees. Their SHA values and acceptance records are
**synthetic only**. They never populate `installer/provider-acceptance.json`.
That production index deliberately starts with `records: []`; configured target
entry hashes come from the reviewed public-source snapshot, while full payload
hashes remain unknown. Passing these tests does not prove native managed-state
initialization or model behavior. No official-source observation was captured during the offline implementation.
The later approved native capability case produced the observed fixtures below.

The Claude `2.1.321 (Claude Code)` official-source fixtures record a **partial**
case: native source-add/install returned zero, user-scope enabled `7.0.0` and
registry pin matched, but the catalog transitioned from `.git` to `.gcs-sha`.
`observed-claude-official-catalog-transition.json` preserves both marketplace
outputs, the before-install verified snapshot, actual marker/entry observations
and native registry evidence. The causing native vector was not isolated.
These are real observations, not a passed source-contract/installer/function
acceptance record. No fixture is copied into the production acceptance index.
