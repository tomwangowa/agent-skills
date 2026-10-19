#!/usr/bin/env python3
"""Worktree bootstrap helper for the task-bootstrap skill.

Every subcommand prints one JSON object on stdout. `delegate` only reads: it locates a repo-local copy of this skill.
"""

from __future__ import annotations

import argparse
import json
import os
import stat
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

GIT_TIMEOUT_SECONDS = 10
# fetch and ls-remote talk to a remote, so they get a longer leash than local git calls.
NETWORK_TIMEOUT_SECONDS = 60

# Used together with `git rev-parse --local-env-vars`: that listing lacks GIT_NAMESPACE and GIT_CEILING_DIRECTORIES,
# which also change what git acts on.
_REPO_ENV_VARS = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_COMMON_DIR",
    "GIT_PREFIX",
    "GIT_NAMESPACE",
    "GIT_CEILING_DIRECTORIES",
)
# These describe how git reads configuration, not which repository it acts on, and test fixtures rely on them.
_KEPT_ENV_VARS = frozenset({"GIT_CONFIG_GLOBAL", "GIT_CONFIG_NOSYSTEM"})

# The skill that is running right now. Resolved so a symlinked ~/.claude/skills still names the real file.
SELF_SKILL: Path = Path(__file__).resolve().parent.parent / "SKILL.md"

# A repo-local variant is a skill directory whose name ends with this (a prefix such as "acme-" is allowed).
_VARIANT_SUFFIX = "task-bootstrap"
# Which tool directory is searched first, per runtime.
_DELEGATE_ORDER = {"claude": (".claude", ".codex"), "codex": (".codex", ".claude")}


@lru_cache(maxsize=1)
def _repo_selecting_env_vars() -> frozenset[str]:
    """Names of the environment variables that make git act on one particular repository."""
    names = set(_REPO_ENV_VARS)
    # Asked with the static names already removed, so the answer cannot depend on what the caller inherited.
    env = {key: value for key, value in os.environ.items() if key not in names}
    try:
        listing = subprocess.run(
            ["git", "rev-parse", "--local-env-vars"],
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
            env=env,
            timeout=GIT_TIMEOUT_SECONDS,
        )
        if listing.returncode == 0:
            names |= {line.strip() for line in listing.stdout.splitlines() if line.strip()}
    except (OSError, subprocess.TimeoutExpired):
        pass
    return frozenset(names - _KEPT_ENV_VARS)


def _git_environment() -> dict[str, str]:
    # An inherited GIT_DIR (set by hooks and some wrappers) outranks `-C`, so every answer would describe that
    # repository instead of the one asked about.
    dropped = _repo_selecting_env_vars()
    env = {key: value for key, value in os.environ.items() if key not in dropped}
    # Never prompt, and never take the index lock for a read: this tool must not disturb a repo someone is using.
    env.update({"GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0"})
    return env


def git(args: list[str], cwd: Path, *, timeout: int = GIT_TIMEOUT_SECONDS) -> subprocess.CompletedProcess[str] | None:
    """Run git in `cwd`; None when git is missing or does not finish in time."""
    # `--source` can name any repository, so keep its config from running a fsmonitor hook.
    command = ["git", "-C", str(cwd), "-c", "core.fsmonitor=false", *args]
    try:
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdin=subprocess.DEVNULL,
            env=_git_environment(),
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


def emit(payload: dict, code: int = 0) -> int:
    stream = sys.stdout
    if hasattr(stream, "reconfigure"):
        # Task text may be CJK; do not let the locale decide whether it can be printed.
        stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    print(json.dumps(payload, ensure_ascii=False), file=stream)
    return code


def user_level_roots(home: Path) -> list[Path]:
    """Directories whose skills belong to the user (or an installed plugin), never to the repository at hand."""
    return [
        home / ".claude" / "skills",
        home / ".codex" / "skills",
        home / ".omp" / "agent" / "skills",
        home / ".claude" / "plugins",
        home / ".codex" / "plugins",
    ]


def _is_under_any(path: Path, roots: list[Path]) -> bool:
    return any(path.is_relative_to(root) for root in roots)


def _variant_names(skills_dir: Path) -> list[str] | None:
    """Names of the entries in `skills_dir` that look like a task-bootstrap variant; None when it cannot be listed."""
    try:
        return sorted(name for name in os.listdir(skills_dir) if name.endswith(_VARIANT_SUFFIX))
    except (FileNotFoundError, NotADirectoryError):
        return []
    except OSError:
        return None


def cmd_delegate(args: argparse.Namespace) -> int:
    cwd = Path(args.cwd) if args.cwd else Path.cwd()
    if not os.path.isdir(cwd):
        return emit({"error": "not_found"}, 2)
    toplevel = git(["rev-parse", "--show-toplevel"], cwd)
    found_root = toplevel is not None and toplevel.returncode == 0 and toplevel.stdout.strip()
    root = Path(os.path.realpath(toplevel.stdout.rstrip("\n") if found_root else cwd))

    # Both spellings of every root: ~/.claude/skills is usually a symlink to another checkout, and a temp HOME may
    # itself sit behind one (/var vs /private/var), so neither form alone matches every candidate.
    home_roots = user_level_roots(Path.home())
    user_roots = [*home_roots, *(Path(os.path.realpath(path)) for path in home_roots)]
    own = SELF_SKILL.resolve()

    candidates: list[dict] = []
    excluded: list[dict[str, str]] = []
    tools: list[str] = []
    found: set[str] = set()
    for tool in _DELEGATE_ORDER[args.runtime]:
        listed = _variant_names(root / tool / "skills")
        if listed is None:
            # A directory that cannot be listed hides the repo's own rules just like an unreadable file does.
            excluded.append({"path": str(root / tool / "skills"), "reason": "unreadable"})
            continue
        tools.append(tool)
        found.update(listed)

    for name in sorted(found):
        kept: list[Path] = []
        contents: list[bytes] = []
        seen: set[Path] = set()
        for tool in tools:
            candidate = root / tool / "skills" / name / "SKILL.md"
            try:
                # os.stat follows symlinks like is_file() does, but Python versions disagree on whether is_file()
                # raises for EACCES; a copy that cannot be read must be reported, not mistaken for an absent one.
                if not stat.S_ISREG(os.stat(candidate).st_mode):
                    continue
            except (FileNotFoundError, NotADirectoryError):
                continue
            except OSError:
                excluded.append({"path": str(candidate), "reason": "unreadable"})
                continue

            real = Path(os.path.realpath(candidate))
            # Delegating to the running skill would loop; the user-level copy shadows repo-local ones by design.
            if real == own:
                excluded.append({"path": str(candidate), "reason": "self"})
                continue
            if _is_under_any(candidate, user_roots) or _is_under_any(real, user_roots):
                excluded.append({"path": str(candidate), "reason": "user_level"})
                continue
            try:
                data = candidate.read_bytes()
            except OSError:
                # The next copy of the same name stands in for it.
                excluded.append({"path": str(candidate), "reason": "unreadable"})
                continue
            if real not in seen:
                seen.add(real)
                kept.append(candidate)
                contents.append(data)

        if kept:
            candidates.append(
                {
                    "name": name,
                    "path": str(kept[0]),
                    # Two spellings of one file were merged above, so a second entry is a separate copy.
                    "drift": len(contents) == 2 and contents[0] != contents[1],
                }
            )

    return emit({"root": str(root), "candidates": candidates, "excluded": excluded})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bootstrap_worktree.py", description="Worktree bootstrap helper for task-bootstrap."
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    delegation = subcommands.add_parser("delegate", help="Find repo-local task-bootstrap variants, if there are any.")
    delegation.add_argument("--runtime", required=True, choices=sorted(_DELEGATE_ORDER), help="Search this tool first.")
    delegation.add_argument("--cwd", help="Directory to start from (default: current directory).")
    delegation.set_defaults(handler=cmd_delegate)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())
