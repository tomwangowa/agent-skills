#!/usr/bin/env bash
# Exercise actual script entry points without reading or writing user settings.
set -euo pipefail
TASK_ROOT="$(cd "$(dirname "$0")/../.." && pwd -P)"
TEMP_ROOT="$(mktemp -d)"
trap 'chmod -R u+w "$TEMP_ROOT"; rm -rf "$TEMP_ROOT"' EXIT
export AGENT_SKILLS_CONFIG_DIR="$TEMP_ROOT/personal settings"
export CLAUDE_SESSION_ID="shared-shell-fixture"
unset CLAUDE_ACTIVITIES_DIR
mkdir -p "$AGENT_SKILLS_CONFIG_DIR" "$TEMP_ROOT/unrelated cwd"
export GUARDED_FIXTURE_ROOT="$TEMP_ROOT"
export GUARDED_REAL_MKDIR="$(command -v mkdir)"
mkdir "$TEMP_ROOT/bin"
cp "$TASK_ROOT/tests/fixtures/guarded_mkdir.py" "$TEMP_ROOT/bin/mkdir"
chmod +x "$TEMP_ROOT/bin/mkdir"
export PATH="$TEMP_ROOT/bin:$PATH"
jq -n '{sources:{activities:"journal",notes:{paths:["notes"]}}}' > "$AGENT_SKILLS_CONFIG_DIR/work-journal.json"

(
 cd "$TEMP_ROOT/unrelated cwd"
 bash "$TASK_ROOT/activity-logger/scripts/init_activities.sh" init > "$TEMP_ROOT/init.out"
 bash "$TASK_ROOT/activity-logger/scripts/log_activity.sh" -d 'shared setting record' > "$TEMP_ROOT/log.out"
)
expected="$AGENT_SKILLS_CONFIG_DIR/journal"
[[ -d "$expected/processed" ]] || { echo 'Initializer did not use the shared activity path' >&2; exit 1; }
record="$(find "$expected" -maxdepth 1 -name '*.json' -print | head -1)"
[[ -n "$record" ]] && jq -e '.activities[0].description == "shared setting record"' "$record" >/dev/null
[[ "$(PYTHONPATH="$TASK_ROOT/runtime" python3 -m agent_skills_runtime.journal_cli activities-dir)" == "$expected" ]]
[[ "$(PYTHONPATH="$TASK_ROOT/runtime" python3 -m agent_skills_runtime.journal_cli config-root)" == "$AGENT_SKILLS_CONFIG_DIR" ]]
bash "$TASK_ROOT/work-log-analyzer/scripts/aggregate_activities.sh" -m json -r all > "$TEMP_ROOT/query.json"
jq -e 'any(.[]; .activities[0].description == "shared setting record")' "$TEMP_ROOT/query.json" >/dev/null
export CLAUDE_ACTIVITIES_DIR="override"
bash "$TASK_ROOT/activity-logger/scripts/log_activity.sh" -d 'overridden record' > "$TEMP_ROOT/override.out"
[[ -d "$AGENT_SKILLS_CONFIG_DIR/override" ]]
PYTHONPATH="$TASK_ROOT/runtime" python3 -m agent_skills_runtime.journal_cli activities-dir | grep -F "$AGENT_SKILLS_CONFIG_DIR/override" >/dev/null

mv "$AGENT_SKILLS_CONFIG_DIR/work-journal.json" "$TEMP_ROOT/saved.json"
if bash "$TASK_ROOT/activity-logger/scripts/log_activity.sh" -d 'must not write' > "$TEMP_ROOT/missing.out" 2>&1; then
 echo 'Missing shared settings unexpectedly succeeded' >&2; exit 1
fi
grep -F 'work-journal.json' "$TEMP_ROOT/missing.out" >/dev/null
printf '{"sources":{"activities":"journal","notes":{"paths":[]}}}\n' > "$AGENT_SKILLS_CONFIG_DIR/work-journal.json"
if bash "$TASK_ROOT/activity-logger/scripts/log_activity.sh" -d 'must not write invalid config' > "$TEMP_ROOT/invalid.out" 2>&1; then
 echo 'Empty notes list unexpectedly succeeded' >&2; exit 1
fi
mv "$TEMP_ROOT/saved.json" "$AGENT_SKILLS_CONFIG_DIR/work-journal.json"
unset CLAUDE_ACTIVITIES_DIR
chmod u-w "$expected"
if [[ ! -w "$expected" ]]; then
 if bash "$TASK_ROOT/activity-logger/scripts/log_activity.sh" -d 'must not write readonly' > "$TEMP_ROOT/readonly.out" 2>&1; then
  echo 'Non-writable activity directory unexpectedly succeeded' >&2; exit 1
 fi
fi
chmod u+w "$expected"
echo 'shared logger config fixture tests passed'
