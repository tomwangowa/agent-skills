#!/bin/bash
set -u
platform=macos
base=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || exit 1
if ! command -v claude >/dev/null 2>&1 && ! command -v codex >/dev/null 2>&1; then
    echo 'Install Claude Code or Codex CLI and configure model access, then rerun. Neither host is installed automatically.'
    exit 1
fi
find_python() {
    for name in python3.13 python3.12 python3.11 python3; do
        candidate=$(command -v "$name" 2>/dev/null) || continue
        if "$candidate" -I -c 'import sys; raise SystemExit(sys.version_info < (3, 11))' >/dev/null 2>&1; then
            printf '%s\n' "$candidate"
            return 0
        fi
    done
    return 1
}
python_path=$(find_python) || python_path=''
if [ -z "$python_path" ]; then
    echo 'Python 3.11+ is required. No plugin installation has started.'
    if ! command -v brew >/dev/null 2>&1; then
        echo 'Install Python 3.11+ manually. Homebrew is not installed automatically.'
        exit 1
    fi
    echo 'Proposed: brew install @@PYTHON_PACKAGE@@'
    echo 'Source: existing Homebrew repositories. Transitive dependencies, downloads and system-path writes may occur; permissions may be requested.'
    printf 'Install Python with the existing manager? [y/N] '
    IFS= read -r answer || exit 130
    case "$answer" in y|Y) ;; *) echo 'Declined. Install Python manually, then rerun.'; exit 130 ;; esac
    export AGENT_SKILLS_BOOTSTRAP_RESULT='Python installation was attempted; earlier system writes may remain.'
    brew install '@@PYTHON_PACKAGE@@'
    manager_exit=$?
    if [ "$manager_exit" -eq 130 ]; then
        echo 'Cancelled during Python installation; earlier writes may remain.'
        exit 130
    fi
    if [ "$manager_exit" -ne 0 ]; then
        echo 'Python installation failed. Earlier writes may remain; no retry or rollback.'
        exit 1
    fi
    python_path=$(find_python) || python_path=''
    if [ -z "$python_path" ]; then
        echo 'Python installation command succeeded but no usable interpreter was found. Check PATH and rerun; prior writes remain.'
        exit 1
    fi
fi
exec "$python_path" -I "$base/install.py" "$@"
