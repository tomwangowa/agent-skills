#!/usr/bin/env python3
"""Worktree bootstrap helper for the task-bootstrap skill.

Every subcommand prints one JSON object on stdout. `delegate` only reads: it locates a repo-local copy of this skill.
`create` works out where a new task's worktree goes, which git commands would make it and which local files would be
copied into it (paths and sizes only, never contents); a refused plan is `{"error": CODE, ...}` with exit code 3.
"""

from __future__ import annotations

import argparse
import json
import os
import posixpath
import re
import stat
import string
import subprocess
import sys
from dataclasses import dataclass
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

WORKTREES_ROOT_ENV = "TASK_BOOTSTRAP_WORKTREES_ROOT"
# Other protocols are refused because a remote URL can name a helper that runs a command ("ext::sh -c ...").
_URL_SCHEMES = ("https://", "ssh://", "git://", "file://")
# [user@]host:path. A host must start with a letter or digit, and the path must not start with ":" or "//", which
# keeps out "ext::cmd", "fd::3" and "http://h/r". No "/" may come before the colon: git reads "a/b:c" as a local path.
_SCP_URL = re.compile(r"(?:[^\s@/:]+@)?[A-Za-z0-9][^\s@/:]*:(?!:|//)\S+")
_SLUG = re.compile(r"[a-z0-9][a-z0-9._-]*")
# str.lower() would also fold characters such as the Kelvin sign into ASCII, which is a silent rewrite of the name.
_ASCII_LOWER = str.maketrans(string.ascii_uppercase, string.ascii_lowercase)

ENV_FILE = ".env"
VENV_DIR = ".venv"
SKILLS_LINK = ".codex/skills"
SKILLS_LINK_TARGET = "../.claude/skills"


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


class Refusal(Exception):
    """A stop condition: nothing was changed, and `code` plus `detail` tell the caller why."""

    def __init__(self, code: str, detail: dict | None = None, *, exit_code: int = 3) -> None:
        super().__init__(code)
        self.code = code
        self.detail = detail or {}
        # 3 is a refusal; 2 is for input that names something that does not exist.
        self.exit_code = exit_code


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


def _git_run(args: list[str], cwd: Path, *, timeout: int = GIT_TIMEOUT_SECONDS) -> subprocess.CompletedProcess[str]:
    """git(), for callers that read the exit status themselves; a missing or hung git is a refusal."""
    result = git(args, cwd, timeout=timeout)
    if result is None:
        raise Refusal("git_unavailable", {"command": args[0]})
    return result


def _git_text(args: list[str], cwd: Path) -> str:
    """stdout of a git call that has no meaningful failure status; any failure is a refusal."""
    result = _git_run(args, cwd)
    if result.returncode != 0:
        lines = result.stderr.strip().splitlines()
        raise Refusal("git_failed", {"command": args[0], "message": lines[0] if lines else ""})
    return result.stdout.rstrip("\n")


def _require_directory(path: Path) -> Path:
    if not os.path.isdir(path):
        raise Refusal("not_found", {"path": str(path)}, exit_code=2)
    return path


def find_main_checkout(anchor: Path) -> Path:
    """The main working tree of the repository `anchor` belongs to, however deep in a linked worktree it is."""
    result = _git_run(["worktree", "list", "--porcelain"], anchor)
    first = result.stdout.split("\n", 1)[0] if result.returncode == 0 else ""
    # The main working tree is always listed first.
    if not first.startswith("worktree "):
        raise Refusal("source_not_git", {"path": str(anchor)})
    return Path(os.path.realpath(first[len("worktree "):]))


def validate_branch(name: str, cwd: Path | None = None) -> str:
    """`name` itself when git accepts it as a branch name; otherwise a refusal."""
    # A leading dash is a legal ref component, but later git commands would read it as an option.
    if not name.startswith("-"):
        result = _git_run(["check-ref-format", "--branch", name], cwd or Path.cwd())
        # --branch expands "@{-1}" to the name of the previously checked out branch; that would silently
        # replace what the user typed, so only a name that comes back unchanged is accepted.
        if result.returncode == 0 and result.stdout.rstrip("\n") == name:
            return name
    raise Refusal("branch_invalid", {"branch": name})


def derive_slug(branch: str) -> str:
    return branch.replace("/", "-").translate(_ASCII_LOWER)


def validate_slug(slug: str) -> str:
    # The slug becomes a directory name, so it must not be able to climb out or look like an option.
    if _SLUG.fullmatch(slug) is None:
        raise Refusal("slug_invalid", {"slug": slug})
    return slug


def remote_url_allowed(url: str) -> bool:
    if not url or url.startswith("-") or any(ch.isspace() or not ch.isprintable() for ch in url):
        return False
    for scheme in _URL_SCHEMES:
        if url.startswith(scheme):
            host = url[len(scheme):].split("/", 1)[0].rpartition("@")[2]
            # file:// has no host. For the others a host starting with a dash would be read as an ssh option.
            return not host.startswith("-") and (bool(host) or scheme == "file://")
    return _SCP_URL.fullmatch(url) is not None


def check_remote(source: Path, remote: str) -> None:
    """The remote must be one of the repository's configured names, with only allowed URLs."""
    names = _git_text(["remote"], source).splitlines()
    if remote.startswith("-") or remote not in names:
        raise Refusal("remote_invalid", {"remote": remote})
    # get-url applies url.<base>.insteadOf, so this is the URL that fetch and ls-remote will really use.
    result = _git_run(["remote", "get-url", remote], source)
    # The URL is not echoed: it may carry credentials.
    if result.returncode != 0 or not remote_url_allowed(result.stdout.rstrip("\n")):
        raise Refusal("remote_url_rejected", {"remote": remote})


def detect_default_branch(source: Path, remote: str, override: str | None) -> str:
    if override is not None:
        try:
            return validate_branch(override, source)
        except Refusal as refusal:
            refusal.detail["option"] = "--default-branch"
            raise
    # The full ref name, not --short: a local branch called "origin/main" would make --short answer "remotes/...".
    prefix = f"refs/remotes/{remote}/"
    result = _git_run(["symbolic-ref", "-q", f"{prefix}HEAD"], source)
    target = result.stdout.strip()
    if result.returncode == 0 and target.startswith(prefix):
        candidate = target[len(prefix):]
        # git checked the ref name when the symbolic ref was written, so only an option-like name needs ruling out.
        if candidate and not candidate.startswith("-"):
            return candidate
    # A remote added with `git remote add` has no HEAD ref until someone runs `set-head`, so ask the remote.
    listing = _git_run(["ls-remote", "--heads", remote, "main", "master"], source, timeout=NETWORK_TIMEOUT_SECONDS)
    if listing.returncode != 0:
        raise Refusal("default_branch_unknown", {"remote": remote, "reason": "ls_remote_failed"})
    # ls-remote patterns match the end of a ref name, so "refs/heads/feature/main" comes back too.
    heads = {line.partition("\t")[2] for line in listing.stdout.splitlines()}
    found = [name for name in ("main", "master") if f"refs/heads/{name}" in heads]
    if len(found) != 1:
        raise Refusal("default_branch_unknown", {"remote": remote, "found": found})
    return found[0]


def check_source_clean(source: Path) -> None:
    # Untracked files do not count: the .env that gets copied into the new worktree is untracked by design.
    changes = _git_text(["status", "--porcelain", "--untracked-files=no"], source).splitlines()
    if changes:
        raise Refusal("source_dirty", {"source": str(source), "entries": len(changes), "changes": changes[:10]})


def check_source_branch(source: Path, expected: str) -> None:
    result = _git_run(["symbolic-ref", "-q", "HEAD"], source)
    ref = result.stdout.strip()
    # A detached HEAD makes symbolic-ref fail, and it never equals a branch name.
    current = ref[len("refs/heads/"):] if result.returncode == 0 and ref.startswith("refs/heads/") else None
    if current != expected:
        raise Refusal("source_branch_mismatch", {"source": str(source), "current": current, "expected": expected})


def check_branch_free(source: Path, branch: str) -> None:
    result = _git_run(["rev-parse", "--verify", "--quiet", f"refs/heads/{branch}"], source)
    if result.returncode == 0:
        raise Refusal("branch_exists", {"branch": branch})
    # --quiet gives 1 for "not there"; anything else means git could not answer, which must not read as "free".
    if result.returncode != 1:
        raise Refusal("git_failed", {"command": "rev-parse", "message": result.stderr.strip()[:200]})


def resolve_names(branch: str, slug: str | None, source: Path) -> tuple[str, str]:
    branch = validate_branch(branch, source)
    # A slug typed by the user is taken as is: quietly "fixing" it would hide a typo.
    return branch, validate_slug(derive_slug(branch) if slug is None else slug)


def resolve_target(worktrees_root: Path, repo_name: str, slug: str) -> Path:
    """Where the worktree will be; `worktrees_root` is passed unresolved so a symlink in it is still visible."""
    # A link here would send the new worktree to wherever it points, so look before resolving anything.
    for parent in (worktrees_root, worktrees_root / repo_name):
        if os.path.islink(parent):
            raise Refusal("parent_symlink", {"path": str(parent)})
    target = Path(os.path.realpath(worktrees_root / repo_name / slug))
    resolved_root = Path(os.path.realpath(worktrees_root))
    if not target.is_relative_to(resolved_root):
        raise Refusal("target_outside_root", {"target": str(target), "worktrees_root": str(resolved_root)})
    # lexists, not exists: a dangling symlink at the target would still break `worktree add`.
    if os.path.lexists(worktrees_root / repo_name / slug):
        raise Refusal("target_exists", {"target": str(target)})
    return target


@dataclass(frozen=True)
class Location:
    main_checkout: Path
    source: Path
    asset_source: Path
    repo_name: str
    # Not resolved, see resolve_target.
    worktrees_root: Path


def _repository_identity(path: Path) -> tuple[bool, Path] | None:
    """(is a work tree, realpath of the common git dir) of the repository `path` is in; None when it is in none."""
    result = _git_run(["rev-parse", "--is-inside-work-tree", "--git-common-dir"], path)
    lines = result.stdout.splitlines()
    if result.returncode != 0 or len(lines) != 2:
        return None
    # Relative to `path` when git runs from inside the repository, and the same for every worktree of it.
    return lines[0] == "true", Path(os.path.realpath(path / lines[1]))


def locate(args: argparse.Namespace) -> Location:
    """Work out the repository, the source and the worktrees root from the cwd and the options."""
    anchor = _require_directory(Path(os.path.abspath(args.cwd or Path.cwd())))
    # The anchor is always the cwd, and the repo name, the default asset source and the default worktrees root come
    # from the repository it belongs to. --source and --asset-source can only pick other checkouts of that same
    # repository, which is verified below.
    main_checkout = find_main_checkout(anchor)

    def option_path(value: str | None, default: Path) -> Path:
        return default if value is None else Path(os.path.realpath(anchor / value))

    source = _require_directory(option_path(args.source, main_checkout))
    asset_source = _require_directory(option_path(args.asset_source, main_checkout))

    known: dict[Path, tuple[bool, Path]] = {}

    def repository_of(role: str, path: Path) -> tuple[bool, Path]:
        if path not in known:
            identity = _repository_identity(path)
            if identity is None:
                raise Refusal("source_not_git", {"role": role, "path": str(path)})
            known[path] = identity
        return known[path]

    _, main_common_dir = repository_of("main_checkout", main_checkout)
    for role, path in (("source", source), ("asset_source", asset_source)):
        is_work_tree, common_dir = repository_of(role, path)
        # A bare repository, or a .git directory, answers "false". The source needs files to check and to branch from,
        # and the asset source needs a work tree because "is it tracked" is answered with ls-files.
        if not is_work_tree:
            raise Refusal("source_not_git", {"role": role, "path": str(path)})
        # Another repository would get a worktree under this one's name, a pull run in it, and (once files are
        # copied) this repository's local files.
        if common_dir != main_common_dir:
            raise Refusal("source_wrong_repo", {"role": role, "path": str(path)})

    configured = args.worktrees_root or os.environ.get(WORKTREES_ROOT_ENV)
    worktrees_root = Path(os.path.abspath(anchor / configured)) if configured else main_checkout.parent / "worktrees"
    return Location(main_checkout, source, asset_source, main_checkout.name, worktrees_root)


def _copy_rejected(reason: str, typed: str) -> Refusal:
    # `typed` is what the user wrote, so they can find it in their own command line.
    return Refusal("copy_rejected", {"path": typed, "reason": reason})


def normalize_copy_path(value: str) -> str:
    """`value` as a path relative to the asset source; a refusal when its shape alone says it is not one."""
    if not value:
        raise _copy_rejected("empty", value)
    # A line break would let one path read as several lines in whatever shows or logs the plan.
    if any(ch in value for ch in "\0\n\r"):
        raise _copy_rejected("invalid_characters", value)
    if value.startswith("/"):
        raise _copy_rejected("absolute", value)
    # Looked for before normpath, which folds "a/../b" into "b" and would hide the climb.
    if ".." in value.split("/"):
        raise _copy_rejected("parent_reference", value)
    return posixpath.normpath(value)


def _lstat(path: Path, typed: str) -> os.stat_result | None:
    """lstat of `path`; None when nothing is there. Any other failure means the asset source cannot be trusted."""
    try:
        return os.lstat(path)
    except (FileNotFoundError, NotADirectoryError):
        return None
    except OSError:
        raise _copy_rejected("unreadable", typed) from None


def _is_tracked(root: Path, relative: str) -> bool:
    # ":(literal)" keeps a name such as "x[1].txt" from being read as a glob that matches another, tracked file.
    # ":(icase)" because on a case-insensitive filesystem "readme.md" finds the tracked README.md on disk while a
    # plain pathspec does not match it. `git config` is not a command this script may run, so it cannot ask whether
    # the repository folds case; on a case-sensitive one this only misreports a name that differs from a tracked one
    # by case alone, which is the safe direction.
    # A failed ls-files prints nothing as well, so a bad exit status has to stop here and never read as "untracked".
    return bool(_git_text(["ls-files", "--", f":(icase,literal){relative}"], root))


def _copy_problem(
    root: Path, relative: str, typed: str, *, directory: bool
) -> tuple[str | None, os.stat_result | None]:
    """(why `relative` cannot be copied, None) or (None, its lstat result)."""
    parent = root / posixpath.dirname(relative)
    real_parent = os.path.realpath(parent)
    # Checked on the parent, not on the entry: a symlink as the last component is "not_regular" below. A link in the
    # middle can lead out of the source, and ls-files answers "nothing" for anything behind one, so a tracked file
    # would pass for untracked. Refusing every such path also covers the links that happen to stay inside.
    if not Path(real_parent).is_relative_to(root):
        return "outside_source", None
    if real_parent != str(parent):
        return "symlink_in_path", None
    # lstat, never stat: a link to a file or a directory is not what was asked for.
    info = _lstat(root / relative, typed)
    if info is None:
        return "absent", None
    if not (stat.S_ISDIR if directory else stat.S_ISREG)(info.st_mode):
        return ("not_directory" if directory else "not_regular"), None
    if _is_tracked(root, relative):
        return "tracked", None
    return None, info


def _directory_bytes(directory: Path, typed: str) -> int:
    """Total size of the regular files under `directory`. Links are neither followed nor counted."""

    def fail(error: OSError) -> None:
        # os.walk skips a directory it cannot list unless told otherwise, which would under-report the size.
        raise error

    total = 0
    try:
        for here, _, names in os.walk(directory, onerror=fail):
            for name in names:
                info = os.lstat(os.path.join(here, name))
                if stat.S_ISREG(info.st_mode):
                    total += info.st_size
    except OSError:
        raise _copy_rejected("unreadable", typed) from None
    return total


def _skills_link(action: str, reason: str | None) -> dict:
    return {"action": action, "path": SKILLS_LINK, "link": SKILLS_LINK_TARGET, "reason": reason}


def plan_skills_link(root: Path) -> dict:
    """Whether the new worktree gets `.codex/skills`: only when the source has exactly that link, and git does not."""
    path = root / SKILLS_LINK
    # ls-files cannot see behind a symlinked directory, so a link found through one could look untracked when it is
    # not. It is reported as not being a link of its own.
    if os.path.realpath(path.parent) != str(path.parent):
        return _skills_link("skip", "not_symlink")
    info = _lstat(path, SKILLS_LINK)
    if info is None:
        return _skills_link("skip", "absent")
    if not stat.S_ISLNK(info.st_mode):
        return _skills_link("skip", "not_symlink")
    try:
        target = os.readlink(path)
    except OSError:
        raise _copy_rejected("unreadable", SKILLS_LINK) from None
    if target != SKILLS_LINK_TARGET:
        return _skills_link("skip", "different_target")
    if _is_tracked(root, SKILLS_LINK):
        return _skills_link("skip", "tracked")
    return _skills_link("create", None)


def plan_local_files(asset_source: Path, copy_venv: bool, extra: list[str]) -> tuple[list[dict], list[dict], dict]:
    """(copies, skipped_copies, symlink) for a worktree whose local files come from `asset_source`.

    Only paths and sizes are gathered; no file is opened. `.env` is looked for without being asked and is skipped
    when it does not qualify. Everything the user asked for (`.venv` with --copy-venv, each --copy) either qualifies
    or the whole plan is refused, because a plan that quietly leaves it out would look like one that includes it.
    """
    # Shapes first, so a malformed request is reported before anything is looked up on disk.
    requested: dict[str, str] = {}
    for value in extra:
        requested.setdefault(normalize_copy_path(value), value)
    root = Path(os.path.realpath(asset_source))
    # Keys are unique, so a request for a path that is already planned adds nothing, and the order is .env, .venv, then
    # the requests as given.
    wanted = dict.fromkeys([ENV_FILE, *([VENV_DIR] if copy_venv else []), *requested])
    copies: list[dict] = []
    skipped: list[dict] = []
    for relative in wanted:
        # .env is the one entry nobody has to ask for; a failure on anything else is a failure to do what was asked.
        asked = relative != ENV_FILE or relative in requested
        typed = requested.get(relative, relative)
        # Without the flag a request for .venv is an ordinary one, and a directory is not a regular file.
        directory = copy_venv and relative == VENV_DIR
        reason, info = _copy_problem(root, relative, typed, directory=directory)
        if reason is not None:
            if asked:
                raise _copy_rejected(reason, typed)
            skipped.append({"path": relative, "reason": reason})
            continue
        size = _directory_bytes(root / relative, typed) if directory else info.st_size
        copies.append({"path": relative, "type": "dir" if directory else "file", "bytes": size})
    return copies, skipped, plan_skills_link(root)


def plan_baseline_local_files(args: argparse.Namespace) -> tuple[list[dict], list[dict], dict]:
    """A baseline copies nothing and never reads the asset source; a request to copy something is refused, not dropped."""
    if args.copy_venv:
        raise _copy_rejected("baseline_mode", VENV_DIR)
    if args.copy:
        raise _copy_rejected("baseline_mode", args.copy[0])
    return [], [], _skills_link("skip", "baseline_mode")


def plan_document(
    args: argparse.Namespace,
    loc: Location,
    *,
    default_branch: str | None,
    base_ref: str,
    branch: str,
    slug: str,
    target: Path,
    commands: list[list[str]],
    local_files: tuple[list[dict], list[dict], dict],
) -> dict:
    """The plan as printed. Every mode fills the same keys, so the caller never has to probe for one."""
    copies, skipped_copies, symlink = local_files
    return {
        "mode": args.mode,
        "task": args.task,
        "source": str(loc.source),
        "asset_source": str(loc.asset_source),
        "remote": args.remote,
        "default_branch": default_branch,
        "base_ref": base_ref,
        "branch": branch,
        "slug": slug,
        "target": str(target),
        "worktrees_root": os.path.realpath(loc.worktrees_root),
        "commands": commands,
        "copies": copies,
        "skipped_copies": skipped_copies,
        "symlink": symlink,
        "executed": False,
    }


def plan_main(args: argparse.Namespace, loc: Location) -> dict:
    source = loc.source
    # The order is part of the contract: it decides which error a caller sees when several things are wrong, and
    # the URL check has to come before anything that could contact the remote.
    check_remote(source, args.remote)
    default_branch = detect_default_branch(source, args.remote, args.default_branch)
    check_source_clean(source)
    check_source_branch(source, default_branch)
    branch, slug = resolve_names(args.branch, args.slug, source)
    check_branch_free(source, branch)
    target = resolve_target(loc.worktrees_root, loc.repo_name, slug)

    base_ref = f"{args.remote}/{default_branch}"
    # Fully qualified: git looks a short name up under refs/heads/ before refs/remotes/, so a local branch called
    # "origin/main" would silently become the start point.
    start_point = f"refs/remotes/{base_ref}"
    base = ["git", "-C", str(source)]
    commands = [
        [*base, "fetch", args.remote],
        [*base, "pull", "--ff-only", args.remote, default_branch],
        # --no-track: a feature branch whose upstream is origin/main is one bare `git push` away from main.
        [*base, "worktree", "add", "--no-track", "-b", branch, str(target), start_point],
    ]
    # Last, so a refusal about the files never hides a problem with the branch or the target.
    local_files = plan_local_files(loc.asset_source, args.copy_venv, args.copy)
    return plan_document(
        args, loc, default_branch=default_branch, base_ref=base_ref, branch=branch, slug=slug, target=target,
        commands=commands, local_files=local_files,
    )


def check_remote_branch(source: Path, remote: str, branch: str) -> None:
    """`branch` must exist on the remote under exactly that name."""
    # The branch name was validated before this, so it cannot be read as an option or as a glob.
    result = _git_run(["ls-remote", "--heads", remote, branch], source, timeout=NETWORK_TIMEOUT_SECONDS)
    if result.returncode != 0:
        # No message: git's complaint about a remote names its URL, which may carry credentials. An unreachable
        # remote must not read as a missing branch either.
        raise Refusal("git_failed", {"command": "ls-remote", "remote": remote})
    # ls-remote patterns match the end of a ref name, so "refs/heads/x/<branch>" comes back too.
    heads = {line.partition("\t")[2] for line in result.stdout.splitlines()}
    if f"refs/heads/{branch}" not in heads:
        raise Refusal("branch_missing_on_remote", {"remote": remote, "branch": branch})


def plan_baseline(args: argparse.Namespace, loc: Location) -> dict:
    source = loc.source
    # A baseline is a copy of a branch that already exists, so it needs neither a clean source nor a default
    # branch, and it does not matter what the source has checked out.
    check_remote(source, args.remote)
    branch, slug = resolve_names(args.branch, args.slug, source)
    check_remote_branch(source, args.remote, branch)
    check_branch_free(source, branch)
    target = resolve_target(loc.worktrees_root, loc.repo_name, slug)

    base_ref = f"{args.remote}/{branch}"
    # Fully qualified for the reason given in plan_main.
    start_point = f"refs/remotes/{base_ref}"
    # An explicit refspec rather than the branch name: a bare name only updates the tracking ref when the remote's
    # configured refspec maps it (a single-branch clone does not), and git resolves a bare name against refs/tags/
    # before refs/heads/, so a tag with the same name would be fetched in place of the branch checked above. The "+"
    # is harmless: the destination is a remote-tracking ref.
    refspec = f"+refs/heads/{branch}:{start_point}"
    base = ["git", "-C", str(source)]
    commands = [
        [*base, "fetch", args.remote, refspec],
        # --track is the whole point here: the local branch follows the remote branch it mirrors.
        [*base, "worktree", "add", "--track", "-b", branch, str(target), start_point],
    ]
    return plan_document(
        args, loc, default_branch=None, base_ref=base_ref, branch=branch, slug=slug, target=target, commands=commands,
        local_files=plan_baseline_local_files(args),
    )


def resolve_commit(source: Path, rev: str) -> str | None:
    """The commit `rev` names in `source`; None when it names nothing, or something that is not a commit."""
    # A leading dash would be read as an option here and again by `worktree add`.
    if not rev or rev.startswith("-"):
        return None
    result = _git_run(["rev-parse", "--verify", "--quiet", f"{rev}^{{commit}}"], source)
    commit = result.stdout.strip()
    return commit if result.returncode == 0 and commit else None


def plan_task(args: argparse.Namespace, loc: Location) -> dict:
    source = loc.source
    # No remote is consulted: the branch grows out of whatever the source already has, remote-tracking or not.
    if not args.base_ref:
        raise Refusal("base_ref_required")
    expected = resolve_commit(source, args.base_ref)
    if expected is None:
        raise Refusal("base_ref_invalid", {"base_ref": args.base_ref})
    check_source_clean(source)
    current = resolve_commit(source, "HEAD")
    # Compared by commit, so a SHA or a detached HEAD at the same commit is as good as the branch name.
    if current != expected:
        raise Refusal(
            "base_ref_mismatch",
            {"source": str(source), "base_ref": args.base_ref, "current": current, "expected": expected},
        )
    branch, slug = resolve_names(args.branch, args.slug, source)
    check_branch_free(source, branch)
    target = resolve_target(loc.worktrees_root, loc.repo_name, slug)

    commands = [
        # --no-track for the reason given in plan_main: the start point may well be a remote-tracking branch.
        ["git", "-C", str(source), "worktree", "add", "--no-track", "-b", branch, str(target), args.base_ref],
    ]
    local_files = plan_local_files(loc.asset_source, args.copy_venv, args.copy)
    return plan_document(
        args, loc, default_branch=None, base_ref=args.base_ref, branch=branch, slug=slug, target=target,
        commands=commands, local_files=local_files,
    )


# One planner per mode: the shared checks above are reused, and only the mode's own sequence differs.
_PLANNERS = {"main": plan_main, "baseline": plan_baseline, "task": plan_task}


def build_plan(args: argparse.Namespace) -> dict:
    if args.execute:
        # Not built yet. Ignoring the flag would look like a plan that was carried out, so say so.
        raise Refusal("option_unsupported", {"option": "--execute"})
    return _PLANNERS[args.mode](args, locate(args))


def cmd_create(args: argparse.Namespace) -> int:
    return emit(build_plan(args))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bootstrap_worktree.py", description="Worktree bootstrap helper for task-bootstrap."
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    delegation = subcommands.add_parser("delegate", help="Find repo-local task-bootstrap variants, if there are any.")
    delegation.add_argument("--runtime", required=True, choices=sorted(_DELEGATE_ORDER), help="Search this tool first.")
    delegation.add_argument("--cwd", help="Directory to start from (default: current directory).")
    delegation.set_defaults(handler=cmd_delegate)

    creation = subcommands.add_parser(
        "create", help="Plan the worktree for a new task; nothing is changed unless --execute is given."
    )
    creation.add_argument("--mode", choices=("main", "baseline", "task"), default="main")
    creation.add_argument("--branch", required=True, help="Name of the branch the worktree is for.")
    creation.add_argument("--slug", help="Directory name of the worktree (default: derived from the branch name).")
    creation.add_argument("--task", help="Task description, copied into the plan unchanged.")
    creation.add_argument(
        "--source", help="Checkout of the same repository to work from (default: the main checkout)."
    )
    creation.add_argument("--base-ref", help="Ref a new branch starts from (task mode).")
    creation.add_argument("--remote", default="origin", help="Name of the remote (default: origin).")
    creation.add_argument("--default-branch", help="Name of the remote's default branch, if it cannot be detected.")
    creation.add_argument(
        "--worktrees-root",
        help=f"Directory that holds the worktrees (default: ${WORKTREES_ROOT_ENV}, then <main checkout>/../worktrees).",
    )
    creation.add_argument(
        "--asset-source", help="Checkout of the same repository that local files come from (default: main checkout)."
    )
    creation.add_argument("--copy-venv", action="store_true", help="Also copy .venv/ (not in baseline mode).")
    creation.add_argument(
        "--copy", action="append", default=[], metavar="PATH",
        help="Untracked regular file in the asset source to copy, relative to it; repeatable (not in baseline mode).",
    )
    creation.add_argument("--execute", action="store_true", help="Carry out the plan instead of only printing it.")
    creation.add_argument("--cwd", help="Directory to start from (default: current directory).")
    creation.set_defaults(handler=cmd_create)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.handler(args)
    except Refusal as refusal:
        return emit({"error": refusal.code, **refusal.detail}, refusal.exit_code)


if __name__ == "__main__":
    sys.exit(main())
