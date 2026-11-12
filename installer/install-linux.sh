#!/bin/bash
set -u
platform=linux
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
    supported=no
    if [ -r /etc/os-release ]; then
        while IFS= read -r line; do
            case "$line" in ID=ubuntu|ID=debian|ID=\"ubuntu\"|ID=\"debian\") supported=yes ;; esac
        done < /etc/os-release
    fi
    if [ "$supported" != yes ] || ! command -v apt-get >/dev/null 2>&1; then
        echo 'Install Python 3.11+ manually. Only an existing Ubuntu/Debian APT manager is supported; no manager is installed.'
        exit 1
    fi
    echo 'Proposed: apt-get install @@PYTHON_PACKAGE@@'
    echo 'Source: configured APT repositories. Transitive dependencies, downloads and system writes may occur. Administrator rights may be required; this script does not elevate privileges.'
    printf 'Install Python with the existing manager? [y/N] '
    IFS= read -r answer || exit 130
    case "$answer" in y|Y) ;; *) echo 'Declined. Install Python manually, then rerun.'; exit 130 ;; esac
    export AGENT_SKILLS_BOOTSTRAP_RESULT='Python installation was attempted; earlier system writes may remain.'
    apt-get install '@@PYTHON_PACKAGE@@'
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
        echo 'The configured repository did not provide a usable Python 3.11+. Check the OS version and PATH; prior writes remain.'
        exit 1
    fi
fi
exec "$python_path" -I "$base/install.py" "$@"
