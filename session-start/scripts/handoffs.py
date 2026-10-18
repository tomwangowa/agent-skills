#!/usr/bin/env python3
"""Read-back helper for the session-start skill: parse handoff files and verify their assertions.

Every subcommand prints one JSON object on stdout. A handoff file is untrusted data: nothing in it is executed or
evaluated except the four whitelisted assertion kinds, and those only run read-only git commands or a stat.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Keep in sync with the assertion table in handoff/SKILL.md; a test compares the two.
ASSERTION_KINDS: tuple[str, ...] = ("expect_head", "branch_is", "file_exists", "worktree_clean")

GIT_TIMEOUT_SECONDS = 10
BOM = b"\xef\xbb\xbf"

_KEY = r"[A-Za-z_][A-Za-z0-9_.-]*"
_TOP_LINE = re.compile(rf"({_KEY}):(?:[ \t]+(.*))?")
_ITEM_LINE = re.compile(rf"( *)-( +)({_KEY}):(?:[ \t]+(.*))?")
_CONTINUATION_LINE = re.compile(rf"( +)({_KEY}):(?:[ \t]+(.*))?")
_COMMENT = re.compile(r"(?:^|\s)#.*$")
_DOUBLE_QUOTED = re.compile(r'"((?:[^"\\]|\\.)*)"(?:\s+#.*)?')
_SINGLE_QUOTED = re.compile(r"'((?:[^']|'')*)'(?:\s+#.*)?")


@dataclass
class ParsedHandoff:
    kind: str  # "ok" | "malformed" | "not_handoff"
    fields: dict[str, str] = field(default_factory=dict)
    assertions: list[dict[str, str]] = field(default_factory=list)
    # Newline-normalised text of everything after the closing fence.
    body: str = ""
    # Byte offset of that text in the original input (BOM and CRLF included), so a rewrite can leave it untouched.
    body_offset: int = 0


def _split_lines(raw: bytes, start: int):
    """Yield (text, end_offset) per line. Only b"\\n" separates lines, so offsets stay exact for CRLF input."""
    position = start
    while position < len(raw):
        newline = raw.find(b"\n", position)
        end = len(raw) if newline == -1 else newline + 1
        yield raw[position:end].decode("utf-8", errors="replace").rstrip("\r\n"), end
        position = end


def _parse_scalar(text: str) -> str | None:
    """Return the scalar text, or None for a flow list/mapping, which the parser does not support."""
    text = text.strip()
    if text.startswith('"'):
        match = _DOUBLE_QUOTED.fullmatch(text)
        if match:
            return re.sub(r'\\(["\\])', r"\1", match.group(1))
    elif text.startswith("'"):
        match = _SINGLE_QUOTED.fullmatch(text)
        if match:
            return match.group(1).replace("''", "'")
    text = _COMMENT.sub("", text).strip()
    # Only a value that is entirely bracketed counts as a collection, so a title like "[WIP] fix x" stays text.
    if (text.startswith("[") and text.endswith("]")) or (text.startswith("{") and text.endswith("}")):
        return None
    return text


def _parse_frontmatter(lines: list[str]) -> tuple[dict[str, str], list[dict[str, str]], bool]:
    """Scan the whole block even after a shape error, so the caller can still tell whether `status` exists."""
    fields: dict[str, str] = {}
    assertions: list[dict[str, str]] = []
    well_formed = True
    in_assertions = False
    seen_assertions = False
    current: dict[str, str] | None = None
    dash_column: int | None = None
    key_column = 0

    def store(target: dict[str, str], key: str, rest: str | None) -> None:
        nonlocal well_formed
        value = _parse_scalar(rest or "")
        if value is None:
            well_formed = False
            value = ""
        if key in target:
            # A repeated key is ambiguous, and would make any later in-place rewrite ambiguous too.
            well_formed = False
        else:
            target[key] = value

    for line in lines:
        line = line.rstrip()
        stripped = line.lstrip(" ")
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(stripped)

        if indent == 0:
            in_assertions = False
            current = None
            match = _TOP_LINE.fullmatch(line)
            if not match:
                well_formed = False
                continue
            key, rest = match.group(1), match.group(2) or ""
            if key != "assertions":
                store(fields, key, rest)
                continue
            if seen_assertions:
                well_formed = False
            seen_assertions = True
            cleaned = _COMMENT.sub("", rest).strip()
            if cleaned == "":
                in_assertions = True
            elif cleaned != "[]":
                well_formed = False
            continue

        # Any indented line outside the assertions list is a nested mapping, list or multi-line scalar.
        if not in_assertions:
            well_formed = False
            continue

        item = _ITEM_LINE.fullmatch(line)
        if item:
            dash = len(item.group(1))
            if dash_column is None:
                dash_column = dash
            elif dash != dash_column:
                well_formed = False
            key_column = dash + 1 + len(item.group(2))
            current = {}
            assertions.append(current)
            store(current, item.group(3), item.group(4))
            continue

        continuation = _CONTINUATION_LINE.fullmatch(line)
        if continuation and current is not None and len(continuation.group(1)) == key_column:
            store(current, continuation.group(2), continuation.group(3))
        else:
            well_formed = False

    return fields, assertions, well_formed


def parse_handoff(raw: bytes) -> ParsedHandoff:
    start = len(BOM) if raw.startswith(BOM) else 0
    lines = _split_lines(raw, start)
    first = next(lines, None)
    if first is None or first[0].rstrip() != "---":
        return ParsedHandoff(kind="not_handoff")

    frontmatter: list[str] = []
    body_offset: int | None = None
    for text, end in lines:
        if text.rstrip() == "---":
            body_offset = end
            break
        frontmatter.append(text)
    if body_offset is None:
        return ParsedHandoff(kind="not_handoff")

    fields, assertions, well_formed = _parse_frontmatter(frontmatter)
    if "status" not in fields:
        return ParsedHandoff(kind="not_handoff")

    body = raw[body_offset:].decode("utf-8", errors="replace").replace("\r\n", "\n")
    return ParsedHandoff(
        kind="ok" if well_formed else "malformed",
        fields=fields,
        # A malformed file must never feed half-parsed assertions to the runner.
        assertions=assertions if well_formed else [],
        body=body,
        body_offset=body_offset,
    )


def split_sections(body: str) -> dict[str, str]:
    """Map each `## ` heading to the text up to the next one; text before the first heading is dropped."""
    sections: dict[str, str] = {}
    key: str | None = None
    for line in body.replace("\r\n", "\n").split("\n"):
        if line.startswith("## "):
            key = line[3:].strip()
            sections.setdefault(key, "")
        elif key is not None:
            sections[key] += line + "\n"
    return sections


def git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str] | None:
    """Run git in `cwd`; None when git is missing or does not finish in time."""
    # The repo path comes from an untrusted handoff, so keep that repo's config from running a fsmonitor hook,
    # and keep `status` from refreshing the index: this helper is read-only.
    command = ["git", "-C", str(cwd), "-c", "core.fsmonitor=false", *args]
    env = {**os.environ, "GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0"}
    try:
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdin=subprocess.DEVNULL,
            env=env,
            timeout=GIT_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


def _first_line(text: str) -> str:
    lines = text.strip().splitlines()
    return lines[0] if lines else ""


def _outcome(kind: str, result: str, detail: str) -> dict[str, str]:
    return {"kind": kind, "result": result, "detail": detail}


def _path_problem(name: str, value: str) -> str | None:
    if not value:
        return f"missing '{name}'"
    if "\x00" in value:
        return f"'{name}' contains a NUL byte"
    if not os.path.isabs(value):
        return f"'{name}' must be an absolute path"
    return None


def run_assertion(item: dict[str, str]) -> dict[str, str]:
    """Evaluate one whitelisted assertion. Anything it cannot evaluate is "unverified", never an exception."""
    kind = item.get("kind", "")
    if kind not in ASSERTION_KINDS:
        return _outcome(kind, "unverified", "unknown assertion kind")

    if kind == "file_exists":
        path = item.get("path", "")
        problem = _path_problem("path", path)
        if problem:
            return _outcome(kind, "unverified", problem)
        try:
            exists = Path(path).exists()
        except OSError as error:
            return _outcome(kind, "unverified", f"cannot stat {path}: {error.strerror or error}")
        return _outcome(kind, "pass" if exists else "fail", f"{path} {'exists' if exists else 'does not exist'}")

    repo = item.get("repo", "")
    problem = _path_problem("repo", repo)
    if problem:
        return _outcome(kind, "unverified", problem)
    value = item.get("value", "")
    # str.startswith("") is True, so an empty value would pass every HEAD; refuse it before any comparison.
    if kind in ("expect_head", "branch_is") and not value:
        return _outcome(kind, "unverified", "missing 'value'")

    repo_path = Path(repo)
    probe = git(["rev-parse", "--is-inside-work-tree"], repo_path)
    if probe is None:
        return _outcome(kind, "unverified", "git is not available")
    if probe.returncode != 0 or probe.stdout.strip() != "true":
        reason = _first_line(probe.stderr)
        return _outcome(kind, "unverified", f"{repo} is not a git work tree" + (f" ({reason})" if reason else ""))

    if kind == "expect_head":
        result = git(["rev-parse", "--verify", "-q", "HEAD"], repo_path)
        if result is None:
            return _outcome(kind, "unverified", "git is not available")
        head = result.stdout.strip()
        if result.returncode != 0 or not head:
            return _outcome(kind, "fail", f"{repo} has no commit at HEAD (expected prefix {value})")
        if head.startswith(value):
            return _outcome(kind, "pass", f"HEAD of {repo} is {head[:12]}, starts with {value}")
        return _outcome(kind, "fail", f"HEAD of {repo} is {head[:12]}, expected prefix {value}")

    if kind == "branch_is":
        result = git(["symbolic-ref", "--short", "-q", "HEAD"], repo_path)
        if result is None:
            return _outcome(kind, "unverified", "git is not available")
        branch = result.stdout.strip()
        if result.returncode == 1 and not branch:
            return _outcome(kind, "fail", f"{repo} has a detached HEAD, expected branch {value}")
        if result.returncode != 0:
            return _outcome(kind, "unverified", f"git symbolic-ref failed: {_first_line(result.stderr)}")
        if branch == value:
            return _outcome(kind, "pass", f"{repo} is on branch {branch}")
        return _outcome(kind, "fail", f"{repo} is on branch {branch}, expected {value}")

    # worktree_clean. Untracked files are named explicitly so a repo-level showUntrackedFiles=no cannot fake "clean".
    result = git(["status", "--porcelain", "--untracked-files=normal"], repo_path)
    if result is None:
        return _outcome(kind, "unverified", "git is not available")
    if result.returncode != 0:
        return _outcome(kind, "unverified", f"git status failed: {_first_line(result.stderr)}")
    changed = len(result.stdout.splitlines())
    if changed == 0:
        return _outcome(kind, "pass", f"{repo} has a clean working tree")
    return _outcome(kind, "fail", f"{repo} has {changed} changed path(s)")


def emit(payload: dict) -> None:
    stream = sys.stdout
    if hasattr(stream, "reconfigure"):
        # Section text is CJK; do not let the locale decide whether it can be printed.
        stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    print(json.dumps(payload, ensure_ascii=False), file=stream)


def _worktree_matches_cwd(fields: dict[str, str], cwd: Path) -> bool | None:
    declared = fields.get("worktree", "")
    if not declared:
        return None
    toplevel = git(["rev-parse", "--show-toplevel"], cwd)
    current = str(cwd)
    if toplevel is not None and toplevel.returncode == 0 and toplevel.stdout.strip():
        current = toplevel.stdout.strip()
    try:
        # realpath on both sides: /var vs /private/var and symlinked checkouts must compare equal.
        return os.path.realpath(os.path.join(cwd, declared)) == os.path.realpath(current)
    except ValueError:
        return False


def command_check(args: argparse.Namespace) -> int:
    path = Path(args.path)
    cwd = Path(args.cwd) if args.cwd else Path.cwd()
    try:
        raw = path.read_bytes()
    except (FileNotFoundError, NotADirectoryError):
        emit({"error": "not_found"})
        return 2
    except OSError as error:
        emit({"error": "unreadable", "detail": error.strerror or str(error)})
        return 2

    parsed = parse_handoff(raw)
    if parsed.kind == "not_handoff":
        emit({"error": "not_handoff"})
        return 2

    status = parsed.fields.get("status", "")
    emit(
        {
            "path": args.path,
            "kind": parsed.kind,
            "status": status,
            "task": parsed.fields.get("task", ""),
            "fields": parsed.fields,
            # parse_handoff already empties this for malformed files.
            "assertions": [run_assertion(item) for item in parsed.assertions],
            "sections": {name: text.strip() for name, text in split_sections(parsed.body).items()},
            # Hash the bytes that were parsed, so a later mark-resumed can detect any change in between.
            "sha256": hashlib.sha256(raw).hexdigest(),
            "already_resumed": status == "resumed",
            "worktree_matches_cwd": _worktree_matches_cwd(parsed.fields, cwd),
        }
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="handoffs.py", description="Handoff read-back helper for session-start.")
    subcommands = parser.add_subparsers(dest="command", required=True)

    check = subcommands.add_parser("check", help="Parse a handoff file and run its whitelisted assertions.")
    check.add_argument("path", help="Path to the handoff file.")
    check.add_argument("--cwd", help="Directory to compare against the handoff's worktree (default: current directory).")
    check.set_defaults(handler=command_check)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())
