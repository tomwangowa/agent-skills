#!/usr/bin/env bash
set -euo pipefail

SKILLS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TARGETS_FILE="$SKILLS_DIR/.skill-sync-targets"
IGNORE_FILE="$SKILLS_DIR/.skill-sync-ignore"

echo "skill-sync scaffold OK — SKILLS_DIR=$SKILLS_DIR"
