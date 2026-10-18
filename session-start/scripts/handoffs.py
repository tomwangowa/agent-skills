#!/usr/bin/env python3
"""Read-back helper for the session-start skill: list, parse, verify and mark handoff files.

Every subcommand prints one JSON object on stdout. A handoff file is untrusted data: nothing in it is executed or
evaluated except the four whitelisted assertion kinds, and those only run read-only git commands or a stat.
`mark-resumed` is the only subcommand that writes: it rewrites the status lines of one handoff and nothing else.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path, PurePath

# Keep in sync with the assertion table in handoff/SKILL.md; a test compares the two.
ASSERTION_KINDS: tuple[str, ...] = ("expect_head", "branch_is", "file_exists", "worktree_clean")

GIT_TIMEOUT_SECONDS = 10
BOM = b"\xef\xbb\xbf"

# `list` shows a short, recent menu by default; `--all` lifts both limits.
LIST_WINDOW = timedelta(days=7)
LIST_LIMIT = 5

# Used only when `git rev-parse --local-env-vars` cannot be asked.
_FALLBACK_REPO_ENV_VARS = (
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


@lru_cache(maxsize=1)
def _repo_selecting_env_vars() -> frozenset[str]:
    """Names of the environment variables that make git act on one particular repository."""
    names: set[str] = set()
    try:
        listing = subprocess.run(
            ["git", "rev-parse", "--local-env-vars"],
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
            timeout=GIT_TIMEOUT_SECONDS,
        )
        if listing.returncode == 0:
            names = {line.strip() for line in listing.stdout.splitlines() if line.strip()}
    except (OSError, subprocess.TimeoutExpired):
        pass
    return frozenset((names or set(_FALLBACK_REPO_ENV_VARS)) - _KEPT_ENV_VARS)


def git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str] | None:
    """Run git in `cwd`; None when git is missing or does not finish in time."""
    # The repo path comes from an untrusted handoff, so keep that repo's config from running a fsmonitor hook,
    # and keep `status` from refreshing the index: this helper is read-only.
    command = ["git", "-C", str(cwd), "-c", "core.fsmonitor=false", *args]
    # An inherited GIT_DIR (set by hooks and some wrappers) outranks `-C`, so every answer would describe that
    # repository instead of the one the handoff names.
    dropped = _repo_selecting_env_vars()
    env = {key: value for key, value in os.environ.items() if key not in dropped}
    env.update({"GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0"})
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


def _resolve_path(name: str, value: str, base: Path | None) -> tuple[str, str | None]:
    """Return (path, None), or ("", reason) when the value cannot be trusted as a location.

    handoff/SKILL.md lets the writer use an absolute path or one relative to the repo. A relative path is anchored
    at the handoff's own `worktree`, never at the reader's cwd, so the answer does not depend on where it runs.
    """
    if not value:
        return "", f"missing '{name}'"
    if os.path.isabs(value):
        path = value
    elif base is not None and os.path.isabs(str(base)):
        path = str(PurePath(str(base), value))
    else:
        return "", f"relative '{name}' needs an absolute 'worktree' in the handoff"
    if "\x00" in path:
        return "", f"'{name}' contains a NUL byte"
    if ".." in PurePath(path).parts:
        return "", f"'{name}' must not contain '..'"
    return path, None


def run_assertion(item: dict[str, str], base: Path | None = None) -> dict[str, str]:
    """Evaluate one whitelisted assertion. Anything it cannot evaluate is "unverified", never an exception.

    `base` is the handoff's `worktree`; it only matters for relative `repo` / `path` values.
    """
    kind = item.get("kind", "")
    if kind not in ASSERTION_KINDS:
        return _outcome(kind, "unverified", "unknown assertion kind")

    if kind == "file_exists":
        path, problem = _resolve_path("path", item.get("path", ""), base)
        if problem:
            return _outcome(kind, "unverified", problem)
        try:
            exists = Path(path).exists()
        except OSError as error:
            return _outcome(kind, "unverified", f"cannot stat {path}: {error.strerror or error}")
        return _outcome(kind, "pass" if exists else "fail", f"{path} {'exists' if exists else 'does not exist'}")

    repo, problem = _resolve_path("repo", item.get("repo", ""), base)
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
    worktree = parsed.fields.get("worktree", "")
    base = Path(worktree) if worktree else None
    emit(
        {
            "path": args.path,
            "kind": parsed.kind,
            "status": status,
            "task": parsed.fields.get("task", ""),
            "fields": parsed.fields,
            # parse_handoff already empties this for malformed files.
            "assertions": [run_assertion(item, base) for item in parsed.assertions],
            "sections": {name: text.strip() for name, text in split_sections(parsed.body).items()},
            # Hash the bytes that were parsed, so a later mark-resumed can detect any change in between.
            "sha256": hashlib.sha256(raw).hexdigest(),
            "already_resumed": status == "resumed",
            "worktree_matches_cwd": _worktree_matches_cwd(parsed.fields, cwd),
        }
    )
    return 0


@dataclass
class Location:
    handoffs_dir: Path
    worktree: Path
    branch: str | None
    current: bool


def _location(worktree: Path, branch: str | None, current: bool) -> Location:
    return Location(worktree / ".claude" / "handoffs", worktree, branch, current)


def _parse_worktree_list(text: str) -> list[tuple[Path, str | None]]:
    """Read `worktree list --porcelain`: blank-line separated records, and a bare repository has no checkout."""
    found: list[tuple[Path, str | None]] = []
    path: str | None = None
    branch: str | None = None
    bare = False
    # The extra "" closes the last record whether or not the output ended with a blank line.
    for line in [*text.splitlines(), ""]:
        if line.startswith("worktree "):
            path, branch, bare = line[len("worktree "):], None, False
        elif line.startswith("branch "):
            branch = line[len("branch "):].removeprefix("refs/heads/")
        elif line == "bare":
            bare = True
        elif line == "" and path is not None:
            if not bare:
                found.append((Path(path), branch))
            path = None
    return found


def discover_locations(cwd: Path) -> tuple[str, list[Location]]:
    """Where handoffs may live: every worktree of the repository around `cwd`, or just `cwd` when git cannot say."""
    toplevel = git(["rev-parse", "--show-toplevel"], cwd)
    if toplevel is None or toplevel.returncode != 0 or not toplevel.stdout.strip():
        return "cwd", [_location(Path(os.path.realpath(cwd)), None, True)]

    # realpath on both sides of every comparison: /var vs /private/var and symlinked checkouts must match.
    top = Path(os.path.realpath(toplevel.stdout.rstrip("\n")))
    listing = git(["worktree", "list", "--porcelain"], top)
    entries = _parse_worktree_list(listing.stdout) if listing is not None and listing.returncode == 0 else []
    locations = [_location(path, branch, os.path.realpath(path) == str(top)) for path, branch in entries]
    if not any(location.current for location in locations):
        # An unusable listing must not hide the handoffs of the checkout the user is standing in.
        locations.insert(0, _location(top, None, True))
    return "git", locations


def _parse_timestamp(value: str | None) -> datetime | None:
    """Parse an ISO 8601 timestamp into an aware datetime; None when it cannot be read."""
    text = (value or "").strip()
    if text[-1:] in ("Z", "z"):
        # fromisoformat only learned the "Z" suffix in Python 3.11.
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
        # A zone-less value is the writer's local time; astimezone() attaches that zone without moving the clock.
        return parsed if parsed.tzinfo is not None else parsed.astimezone()
    except (ValueError, OverflowError, OSError):
        return None


def _resolve_now(value: str | None) -> datetime | None:
    """The `--now` override, else the current local time with its offset; None when the override cannot be read."""
    return datetime.now().astimezone() if value is None else _parse_timestamp(value)


def parse_created(value: str | None, fallback_mtime: float) -> datetime:
    """Aware datetime for a handoff's `created`; the file's mtime stands in when it is missing or unreadable."""
    parsed = _parse_timestamp(value)
    if parsed is not None:
        return parsed
    try:
        return datetime.fromtimestamp(fallback_mtime, tz=timezone.utc).astimezone()
    except (ValueError, OverflowError, OSError):
        return datetime.fromtimestamp(0, tz=timezone.utc)


def _scan_handoffs(location: Location) -> tuple[list[tuple[datetime, dict]], list[dict[str, str]]]:
    """Read the top-level *.md files of one handoffs directory; files that cannot be read or trusted go to `skipped`."""
    found: list[tuple[datetime, dict]] = []
    skipped: list[dict[str, str]] = []
    try:
        names = sorted(os.listdir(location.handoffs_dir))
    except (FileNotFoundError, NotADirectoryError):
        return found, skipped
    except OSError:
        return found, [{"path": str(location.handoffs_dir), "reason": "unreadable"}]

    for name in names:
        if not name.endswith(".md"):
            continue
        path = location.handoffs_dir / name
        try:
            # lstat, not stat: a symlink can point anywhere on disk, so it has to be seen as one.
            info = os.lstat(path)
            if stat.S_ISLNK(info.st_mode):
                skipped.append({"path": str(path), "reason": "symlink"})
                continue
            if not stat.S_ISREG(info.st_mode):
                # A directory or FIFO named *.md is no handoff, and reading a FIFO would block.
                continue
            raw = path.read_bytes()
        except OSError:
            skipped.append({"path": str(path), "reason": "unreadable"})
            continue

        parsed = parse_handoff(raw)
        status = parsed.fields.get("status")
        if status == "resumed":
            continue
        created = parse_created(parsed.fields.get("created"), info.st_mtime)
        item = {
            "path": str(path),
            "task": parsed.fields.get("task", ""),
            "status": status,
            "created": created.isoformat(),
            "worktree": str(location.worktree),
            "branch": location.branch,
            "current": location.current,
            # A blank status cannot say whether the work is finished, so it is flagged like a broken file.
            "malformed": parsed.kind != "ok" or status == "",
        }
        found.append((created, item))
    return found, skipped


def command_list(args: argparse.Namespace) -> int:
    cwd = Path(args.cwd) if args.cwd else Path.cwd()
    now = _resolve_now(args.now)
    if now is None:
        emit({"error": "invalid_now"})
        return 2

    scope, locations = discover_locations(cwd)
    found: list[tuple[datetime, dict]] = []
    skipped: list[dict[str, str]] = []
    for location in locations:
        if not os.path.isdir(location.worktree):
            # `git worktree list` keeps naming a checkout that was deleted without `git worktree prune`.
            skipped.append({"path": str(location.worktree), "reason": "missing_worktree"})
            continue
        entries, problems = _scan_handoffs(location)
        found += entries
        skipped += problems

    # The path is the last key so equal timestamps still give the same order on every run.
    found.sort(key=lambda entry: (not entry[1]["current"], -entry[0].timestamp(), entry[1]["path"]))
    if args.all:
        shown = found
    else:
        cutoff = now - LIST_WINDOW
        shown = [entry for entry in found if entry[0] >= cutoff][:LIST_LIMIT]
    # `remaining` is what `--all` would add, so a handoff hidden for being stale is still announced, not lost silently.
    emit(
        {
            "scope": scope,
            "items": [item for _, item in shown],
            "remaining": len(found) - len(shown),
            "skipped": skipped,
        }
    )
    return 0


def _line_ending(line: bytes) -> bytes:
    return b"\r\n" if line.endswith(b"\r\n") else b"\n"


def _frontmatter_spans(raw: bytes, keys: tuple[str, ...]) -> dict[str, tuple[int, int]]:
    """Byte span of each top-level `key:` line in the frontmatter, found with the same rules parse_handoff uses."""
    lines = _split_lines(raw, len(BOM) if raw.startswith(BOM) else 0)
    _, position = next(lines)  # the opening fence; parse_handoff has already vouched for it
    spans: dict[str, tuple[int, int]] = {}
    for text, end in lines:
        if text.rstrip() == "---":
            break
        match = _TOP_LINE.fullmatch(text.rstrip())
        if match and match.group(1) in keys:
            spans[match.group(1)] = (position, end)
        position = end
    return spans


def _rewrite_as_resumed(raw: bytes, resumed_at: str) -> bytes | None:
    """Swap the `status` line for `resumed` and set `resumed_at`; every other byte stays, line endings included."""
    spans = _frontmatter_spans(raw, ("status", "resumed_at"))
    if "status" not in spans:
        return None
    start, end = spans["status"]
    ending = _line_ending(raw[start:end])
    stamp = f"resumed_at: {resumed_at}".encode("utf-8")
    if "resumed_at" in spans:
        # Replace the old line where it stands: a second `resumed_at` would make the key ambiguous.
        old_start, old_end = spans["resumed_at"]
        edits = [
            (start, end, b"status: resumed" + ending),
            (old_start, old_end, stamp + _line_ending(raw[old_start:old_end])),
        ]
    else:
        edits = [(start, end, b"status: resumed" + ending + stamp + ending)]
    # Back to front, so the earlier offsets are still valid after each splice.
    for edit_start, edit_end, text in sorted(edits, reverse=True):
        raw = raw[:edit_start] + text + raw[edit_end:]
    return raw


def _rewrite_is_faithful(before: ParsedHandoff, raw: bytes, updated: bytes, resumed_at: str) -> bool:
    """True only if `updated` parses to the old handoff with just status and resumed_at changed, body bytes equal."""
    after = parse_handoff(updated)
    return (
        after.kind == "ok"
        and after.fields == {**before.fields, "status": "resumed", "resumed_at": resumed_at}
        and after.assertions == before.assertions
        and updated[after.body_offset:] == raw[before.body_offset:]
    )


def _replace_file(path: Path, data: bytes, mode: int) -> None:
    """Swap `data` in through a temp file in the same directory, so a reader sees the old file or the new one."""
    # A short fixed prefix keeps a long CJK handoff name under the filesystem's name limit, and the .tmp suffix keeps
    # a leftover from a crash out of `list`, which only reads *.md.
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=".handoff-", suffix=".tmp")
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        # mkstemp creates 0600. Restoring the mode after the write also lets a read-only original be replaced.
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def _refuse(error: str) -> int:
    emit({"error": error})
    return 3


def command_mark_resumed(args: argparse.Namespace) -> int:
    # Settle the arguments before touching the file.
    now = _resolve_now(args.now)
    if now is None:
        emit({"error": "invalid_now"})
        return 2

    path = Path(args.path)
    try:
        # lstat before any read: a symlink must be refused as one, and opening a FIFO would block.
        info = os.lstat(path)
        if stat.S_ISLNK(info.st_mode):
            return _refuse("symlink")
        if not stat.S_ISREG(info.st_mode):
            return _refuse("not_handoff")
        raw = path.read_bytes()
    except (FileNotFoundError, NotADirectoryError):
        emit({"error": "not_found"})
        return 2
    except OSError as error:
        emit({"error": "unreadable", "detail": error.strerror or str(error)})
        return 2

    if hashlib.sha256(raw).hexdigest() != args.expect_sha256:
        return _refuse("hash_mismatch")
    parsed = parse_handoff(raw)
    if parsed.kind != "ok":
        return _refuse(parsed.kind)
    if parsed.fields["status"] == "resumed":
        return _refuse("already_resumed")

    resumed_at = now.isoformat(timespec="seconds")
    updated = _rewrite_as_resumed(raw, resumed_at)
    # Re-parse what is about to be written: a surprise must end in a refusal, never in a half-right user file.
    if updated is None or not _rewrite_is_faithful(parsed, raw, updated, resumed_at):
        return _refuse("malformed")
    try:
        _replace_file(path, updated, stat.S_IMODE(info.st_mode))
    except OSError as error:
        emit({"error": "unwritable", "detail": error.strerror or str(error)})
        return 2
    emit({"path": args.path, "status": "resumed", "resumed_at": resumed_at})
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="handoffs.py", description="Handoff read-back helper for session-start.")
    subcommands = parser.add_subparsers(dest="command", required=True)

    check = subcommands.add_parser("check", help="Parse a handoff file and run its whitelisted assertions.")
    check.add_argument("path", help="Path to the handoff file.")
    check.add_argument("--cwd", help="Directory to compare against the handoff's worktree (default: current directory).")
    check.set_defaults(handler=command_check)

    listing = subcommands.add_parser("list", help="List unfinished handoffs across the repository's worktrees.")
    listing.add_argument("--all", action="store_true", help="Lift the 7-day window and the 5-item cap.")
    listing.add_argument("--cwd", help="Directory to start from (default: current directory).")
    listing.add_argument("--now", help="ISO 8601 timestamp to use as the current time; for tests.")
    listing.set_defaults(handler=command_list)

    resume = subcommands.add_parser("mark-resumed", help="Mark one handoff resumed; the only subcommand that writes.")
    resume.add_argument("path", help="Path to the handoff file.")
    resume.add_argument("--expect-sha256", required=True, help="The sha256 from `check`; refuse if the file changed.")
    resume.add_argument("--now", help="ISO 8601 timestamp to use as the current time; for tests.")
    resume.set_defaults(handler=command_mark_resumed)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())
