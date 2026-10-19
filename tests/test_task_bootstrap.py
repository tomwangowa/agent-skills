"""Tests for task-bootstrap/scripts/bootstrap_worktree.py: the delegate subcommand and the shared test fixtures."""

from __future__ import annotations

import atexit
import contextlib
import functools
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path
from unittest import mock


SOURCE_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = SOURCE_ROOT / "task-bootstrap" / "scripts" / "bootstrap_worktree.py"
SESSION_START_SCRIPT = SOURCE_ROOT / "session-start" / "scripts" / "handoffs.py"

# The host's global git config may set core.excludesFile, sign commits or install hooks; none of that may leak
# into a fixture. Author and committer are pinned so commits work on a machine with no identity configured.
GIT_ENV = {
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    # The default global ignore file lives under XDG, not in any config file, so point it at nothing too.
    "XDG_CONFIG_HOME": os.path.join(os.devnull, "xdg"),
    "GIT_AUTHOR_NAME": "Fixture Author",
    "GIT_AUTHOR_EMAIL": "author@example.invalid",
    "GIT_COMMITTER_NAME": "Fixture Committer",
    "GIT_COMMITTER_EMAIL": "committer@example.invalid",
}

# Not a GIT_* variable, but it moves every `target` the script computes, so a developer's own setting must not leak.
_HOST_SETTINGS = ("TASK_BOOTSTRAP_WORKTREES_ROOT",)


@functools.cache
def _scratch_home() -> str:
    """A HOME for callers that name none, so a child process can never fall through to the real `~`."""
    path = tempfile.mkdtemp(prefix="task-bootstrap-test-home-")
    atexit.register(shutil.rmtree, path, ignore_errors=True)
    return path


def load_module(path: Path, name: str):
    """Import a script by path; it is not a package member."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    # @dataclass resolves string annotations through sys.modules, so register before executing.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def isolated_env(extra: dict | None = None) -> dict:
    """Environment for every git call and CLI run: no inherited GIT_* (a pre-commit hook sets GIT_DIR) plus GIT_ENV."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_") and k not in _HOST_SETTINGS}
    env["HOME"] = _scratch_home()
    env.update(GIT_ENV)
    env.update(extra or {})
    return env


def run_git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(
        ["git", "-C", str(cwd), *args],
        env=isolated_env(),
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed ({result.returncode}) in {cwd}: {result.stderr.strip()}")
    return result


def git_out(cwd: Path, *args: str) -> str:
    """stdout of a git command run in `cwd`, without the trailing newline; raises if git fails."""
    return run_git(cwd, *args).stdout.rstrip("\n")


@dataclass
class Project:
    tmp: Path  # resolved, so it compares equal to what git and the script print
    origin: Path  # bare repository
    main: Path  # clone of origin, on branch main


def make_project(tmp: Path) -> Project:
    """A clone of a local bare remote: one commit on main, pushed, upstream set, origin/HEAD set."""
    # On macOS /var is a symlink to /private/var; git and the script print the resolved spelling.
    tmp = tmp.resolve()
    (tmp / "home").mkdir(exist_ok=True)
    origin = tmp / "origin.git"
    main = tmp / "proj"
    run_git(tmp, "init", "-q", "--bare", "-b", "main", str(origin))
    run_git(tmp, "clone", "-q", origin.as_uri(), str(main))
    # An empty clone leaves HEAD unborn on whatever init.defaultBranch says, so pin the name before committing.
    run_git(main, "symbolic-ref", "HEAD", "refs/heads/main")
    (main / "README.md").write_text("fixture\n", encoding="utf-8")
    run_git(main, "add", "README.md")
    run_git(main, "commit", "-q", "-m", "init")
    run_git(main, "push", "-q", "-u", "origin", "main")
    # A push never creates origin/HEAD, but a real clone of a non-empty remote has it.
    run_git(main, "remote", "set-head", "origin", "main")
    return Project(tmp=tmp, origin=origin, main=main)


def _run_cli(script: Path, *args: str, cwd: Path, env: dict | None = None) -> tuple[int, dict]:
    """Run a copy of the CLI in a subprocess; env entries are merged over the isolated environment."""
    result = subprocess.run(
        [sys.executable, str(script), *args],
        cwd=str(cwd),
        env=isolated_env(env),
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
    )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise AssertionError(
            f"stdout is not JSON (exit {result.returncode}): {result.stdout!r}; stderr: {result.stderr!r}"
        ) from error
    return result.returncode, payload


def run_script(*args: str, cwd: Path, env: dict | None = None) -> tuple[int, dict]:
    """Run the CLI under test. HOME is the scratch home unless `env` names one."""
    return _run_cli(SCRIPT, *args, cwd=cwd, env=env)


def run_create(project: Project, *args: str, cwd: Path | None = None) -> tuple[int, dict]:
    """Run `create` from the project's main checkout (or `cwd`) with HOME inside the project's temp dir."""
    return run_script("create", *args, cwd=cwd or project.main, env={"HOME": str(project.tmp / "home")})


class TempProjectCase(unittest.TestCase):
    """A throwaway project in a temp dir that is removed afterwards."""

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project = make_project(Path(temporary.name))
        self.tmp = self.project.tmp
        self.root = self.project.main
        self.home = self.tmp / "home"


class DelegateTests(TempProjectCase):
    """`delegate` runs a copy of the script from install/, so "self" never coincides with a candidate unless a test
    wants it to."""

    def setUp(self) -> None:
        super().setUp()
        self.install = self.tmp / "install" / "task-bootstrap"
        (self.install / "scripts").mkdir(parents=True)
        (self.install / "SKILL.md").write_text("generic\n", encoding="utf-8")
        self.script = self.install / "scripts" / "bootstrap_worktree.py"
        shutil.copy2(SCRIPT, self.script)

    @staticmethod
    def skill(skills_dir: Path, name: str = "acme-task-bootstrap", text: str = "local\n") -> Path:
        path = skills_dir / name / "SKILL.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def run_delegate(self, runtime: str, *args: str, cwd: Path | None = None, script: Path | None = None,
                     env: dict | None = None) -> tuple[int, dict]:
        return _run_cli(
            script or self.script, "delegate", "--runtime", runtime, *args,
            cwd=cwd or self.root, env={"HOME": str(self.home), **(env or {})},
        )

    def delegate(self, runtime: str, *args: str, cwd: Path | None = None, script: Path | None = None,
                 env: dict | None = None) -> dict:
        code, out = self.run_delegate(runtime, *args, cwd=cwd, script=script, env=env)
        self.assertEqual(code, 0)
        return out

    def test_no_candidate_returns_empty(self) -> None:
        out = self.delegate("claude")
        self.assertEqual(set(out), {"root", "candidates", "excluded"})
        self.assertEqual(out["candidates"], [])
        self.assertEqual(out["excluded"], [])
        self.assertEqual(Path(out["root"]), self.root)

    def test_prefixed_variant_found(self) -> None:
        path = self.skill(self.root / ".claude" / "skills", "acme-task-bootstrap")
        out = self.delegate("claude")
        self.assertEqual(out["candidates"], [{"name": "acme-task-bootstrap", "path": str(path), "drift": False}])
        self.assertEqual(out["excluded"], [])

    def test_plain_task_bootstrap_name_counts(self) -> None:
        path = self.skill(self.root / ".claude" / "skills", "task-bootstrap")
        out = self.delegate("claude")
        self.assertEqual(out["candidates"], [{"name": "task-bootstrap", "path": str(path), "drift": False}])

    def test_other_directory_names_are_ignored(self) -> None:
        skills = self.root / ".claude" / "skills"
        for name in ("session-start", "task-bootstrap-notes", "bootstrap"):
            self.skill(skills, name)
        self.assertEqual(self.delegate("claude")["candidates"], [])

    def test_several_variants_sorted_by_name(self) -> None:
        skills = self.root / ".claude" / "skills"
        # Written out of order, and one on each side, so neither disk order nor scan order can explain the result.
        self.skill(skills, "zeta-task-bootstrap")
        self.skill(self.root / ".codex" / "skills", "beta-task-bootstrap")
        self.skill(skills, "acme-task-bootstrap")
        out = self.delegate("claude")
        self.assertEqual([entry["name"] for entry in out["candidates"]],
                         ["acme-task-bootstrap", "beta-task-bootstrap", "zeta-task-bootstrap"])

    def test_runtime_order_and_drift(self) -> None:
        self.skill(self.root / ".claude" / "skills", text="claude copy\n")
        self.skill(self.root / ".codex" / "skills", text="codex copy\n")
        for runtime, first in (("claude", ".claude"), ("codex", ".codex")):
            with self.subTest(runtime=runtime):
                out = self.delegate(runtime)
                self.assertEqual(len(out["candidates"]), 1)
                self.assertIn(f"/{first}/skills/", out["candidates"][0]["path"])
                self.assertIs(out["candidates"][0]["drift"], True)
                self.assertEqual(out["excluded"], [])

    def test_identical_distinct_files_report_no_drift(self) -> None:
        self.skill(self.root / ".claude" / "skills", text="same\n")
        self.skill(self.root / ".codex" / "skills", text="same\n")
        self.assertIs(self.delegate("claude")["candidates"][0]["drift"], False)

    def test_drift_is_judged_per_name(self) -> None:
        self.skill(self.root / ".claude" / "skills", "acme-task-bootstrap", "one\n")
        self.skill(self.root / ".codex" / "skills", "acme-task-bootstrap", "two\n")
        self.skill(self.root / ".claude" / "skills", "beta-task-bootstrap", "alone\n")
        drift = {entry["name"]: entry["drift"] for entry in self.delegate("claude")["candidates"]}
        self.assertEqual(drift, {"acme-task-bootstrap": True, "beta-task-bootstrap": False})

    def test_symlinked_codex_dir_dedupes(self) -> None:
        self.skill(self.root / ".claude" / "skills")
        (self.root / ".codex").mkdir()
        (self.root / ".codex" / "skills").symlink_to(Path("..") / ".claude" / "skills")
        for runtime, first in (("claude", ".claude"), ("codex", ".codex")):
            with self.subTest(runtime=runtime):
                out = self.delegate(runtime)
                self.assertEqual(len(out["candidates"]), 1)
                # The first candidate in runtime order is kept, under the spelling it was found by.
                self.assertIn(f"/{first}/skills/acme-task-bootstrap/SKILL.md", out["candidates"][0]["path"])
                self.assertIs(out["candidates"][0]["drift"], False)
                self.assertEqual(out["excluded"], [])

    def test_self_is_excluded(self) -> None:
        own = self.root / ".claude" / "skills" / "task-bootstrap"
        (own / "scripts").mkdir(parents=True)
        shutil.copy2(SCRIPT, own / "scripts" / "bootstrap_worktree.py")
        (own / "SKILL.md").write_text("this is the running skill\n", encoding="utf-8")
        out = self.delegate("claude", script=own / "scripts" / "bootstrap_worktree.py")
        self.assertEqual(out["candidates"], [])
        self.assertEqual([entry["reason"] for entry in out["excluded"]], ["self"])
        self.assertTrue(out["excluded"][0]["path"].endswith("/.claude/skills/task-bootstrap/SKILL.md"))

    def test_self_excluded_but_the_prefixed_variant_still_delegates(self) -> None:
        own = self.root / ".claude" / "skills" / "task-bootstrap"
        (own / "scripts").mkdir(parents=True)
        shutil.copy2(SCRIPT, own / "scripts" / "bootstrap_worktree.py")
        (own / "SKILL.md").write_text("this is the running skill\n", encoding="utf-8")
        self.skill(self.root / ".claude" / "skills", "acme-task-bootstrap")
        out = self.delegate("claude", script=own / "scripts" / "bootstrap_worktree.py")
        self.assertEqual([entry["name"] for entry in out["candidates"]], ["acme-task-bootstrap"])
        self.assertEqual([entry["reason"] for entry in out["excluded"]], ["self"])

    def test_production_layout_is_self(self) -> None:
        # ~/.claude/skills points at a separate checkout, and the skill runs through that symlink.
        prod = self.tmp / "prod"
        self.skill(prod, "task-bootstrap", "user-level\n")
        (prod / "task-bootstrap" / "scripts").mkdir()
        shutil.copy2(SCRIPT, prod / "task-bootstrap" / "scripts" / "bootstrap_worktree.py")
        (self.home / ".claude").mkdir()
        (self.home / ".claude" / "skills").symlink_to(prod)
        script = self.home / ".claude" / "skills" / "task-bootstrap" / "scripts" / "bootstrap_worktree.py"
        out = self.delegate("claude", "--cwd", str(self.home), script=script)
        self.assertEqual(out["candidates"], [])
        self.assertEqual([entry["reason"] for entry in out["excluded"]], ["self"])

    def test_user_level_excluded(self) -> None:
        prod = self.tmp / "prod"
        self.skill(prod, "acme-task-bootstrap")
        (self.home / ".claude").mkdir()
        (self.home / ".claude" / "skills").symlink_to(prod)
        # --cwd arrives as the literal spelling, unlike a process cwd, which the OS reports already resolved.
        out = self.delegate("claude", "--cwd", str(self.home), cwd=self.tmp)
        self.assertEqual(out["candidates"], [])
        self.assertEqual([entry["reason"] for entry in out["excluded"]], ["user_level"])
        self.assertEqual(Path(out["root"]), self.home)

    def test_user_level_skill_that_is_a_symlink_elsewhere_is_excluded(self) -> None:
        # The target's realpath is under no user-level root, so only the candidate's own spelling can match.
        target = self.tmp / "elsewhere" / "SKILL.md"
        target.parent.mkdir()
        target.write_text("user-level\n", encoding="utf-8")
        link = self.home / ".claude" / "skills" / "acme-task-bootstrap" / "SKILL.md"
        link.parent.mkdir(parents=True)
        link.symlink_to(target)
        out = self.delegate("claude", "--cwd", str(self.home), cwd=self.tmp)
        self.assertEqual(out["candidates"], [])
        self.assertEqual([entry["reason"] for entry in out["excluded"]], ["user_level"])

    def test_repo_skills_dir_linked_into_user_level_is_excluded(self) -> None:
        self.skill(self.home / ".claude" / "skills", text="user-level\n")
        (self.root / ".claude").mkdir()
        (self.root / ".claude" / "skills").symlink_to(self.home / ".claude" / "skills")
        local = self.skill(self.root / ".codex" / "skills", text="repo-local\n")
        out = self.delegate("claude")
        self.assertEqual([entry["path"] for entry in out["candidates"]], [str(local)])
        self.assertEqual([entry["reason"] for entry in out["excluded"]], ["user_level"])

    def test_plugin_roots_are_user_level(self) -> None:
        (self.root / ".claude").mkdir()
        link = self.root / ".claude" / "skills"
        for tool in (".claude", ".codex"):
            with self.subTest(tool=tool):
                cache = self.home / tool / "plugins" / "cache" / "x"
                self.skill(cache, text="plugin copy\n")
                link.unlink(missing_ok=True)
                link.symlink_to(cache)
                out = self.delegate("claude")
                self.assertEqual(out["candidates"], [])
                self.assertEqual([entry["reason"] for entry in out["excluded"]], ["user_level"])

    @unittest.skipIf(hasattr(os, "geteuid") and os.geteuid() == 0, "root ignores file permissions")
    def test_unreadable_candidate_falls_to_next(self) -> None:
        # Dropping it silently would hide the repo's own rules, so it has to show up in `excluded`.
        unreadable = self.skill(self.root / ".claude" / "skills")
        unreadable.chmod(0)
        self.addCleanup(unreadable.chmod, 0o644)
        readable = self.skill(self.root / ".codex" / "skills")
        out = self.delegate("claude")
        self.assertEqual(out["candidates"], [{"name": "acme-task-bootstrap", "path": str(readable), "drift": False}])
        self.assertEqual(out["excluded"], [{"path": str(unreadable), "reason": "unreadable"}])

    @unittest.skipIf(hasattr(os, "geteuid") and os.geteuid() == 0, "root ignores file permissions")
    def test_unlistable_skills_dir_is_reported_not_hidden(self) -> None:
        self.skill(self.root / ".claude" / "skills")
        locked = self.root / ".codex" / "skills"
        self.skill(locked, "beta-task-bootstrap")
        locked.chmod(0)
        self.addCleanup(locked.chmod, 0o755)
        out = self.delegate("claude")
        self.assertEqual([entry["name"] for entry in out["candidates"]], ["acme-task-bootstrap"])
        self.assertEqual(out["excluded"], [{"path": str(locked), "reason": "unreadable"}])

    def test_non_regular_or_dangling_candidates_are_ignored(self) -> None:
        (self.root / ".claude" / "skills" / "acme-task-bootstrap" / "SKILL.md").mkdir(parents=True)
        dangling = self.root / ".codex" / "skills" / "beta-task-bootstrap" / "SKILL.md"
        dangling.parent.mkdir(parents=True)
        dangling.symlink_to(self.tmp / "missing.md")
        out = self.delegate("claude")
        self.assertEqual((out["candidates"], out["excluded"]), ([], []))

    def test_dangling_skills_dir_is_ignored(self) -> None:
        (self.root / ".claude").mkdir()
        (self.root / ".claude" / "skills").symlink_to(self.tmp / "missing")
        out = self.delegate("claude")
        self.assertEqual((out["candidates"], out["excluded"]), ([], []))

    def test_non_git_uses_cwd_root(self) -> None:
        plain = self.tmp / "plain"
        path = self.skill(plain / ".claude" / "skills")
        out = self.delegate("claude", cwd=plain)
        self.assertEqual(Path(out["root"]), plain)
        self.assertEqual([entry["path"] for entry in out["candidates"]], [str(path)])

    def test_git_root_is_used_from_a_subdirectory(self) -> None:
        self.skill(self.root / ".claude" / "skills")
        sub = self.root / "pkg" / "deep"
        sub.mkdir(parents=True)
        out = self.delegate("claude", cwd=sub)
        self.assertEqual(Path(out["root"]), self.root)
        self.assertEqual(len(out["candidates"]), 1)

    def test_cwd_option_overrides_process_cwd(self) -> None:
        self.skill(self.root / ".claude" / "skills")
        out = self.delegate("claude", "--cwd", str(self.root), cwd=self.tmp)
        self.assertEqual(Path(out["root"]), self.root)
        self.assertEqual(len(out["candidates"]), 1)

    def test_git_unavailable_falls_back_to_cwd(self) -> None:
        self.skill(self.root / ".claude" / "skills")
        sub = self.root / "pkg"
        sub.mkdir()
        nested = self.skill(sub / ".claude" / "skills", text="nested\n")
        empty_bin = self.tmp / "empty-bin"
        empty_bin.mkdir()
        self.assertIsNone(shutil.which("git", path=str(empty_bin)))
        self.assertEqual(Path(self.delegate("claude", cwd=sub)["root"]), self.root)
        # _run_cli launches the absolute sys.executable, so an empty PATH removes git and nothing else.
        out = self.delegate("claude", cwd=sub, env={"PATH": str(empty_bin)})
        self.assertEqual(Path(out["root"]), sub)
        self.assertEqual([entry["path"] for entry in out["candidates"]], [str(nested)])

    def test_missing_cwd_exits_2(self) -> None:
        self.assertEqual(
            self.run_delegate("claude", "--cwd", str(self.tmp / "nope"), cwd=self.tmp), (2, {"error": "not_found"})
        )

    def test_cwd_that_is_a_file_exits_2(self) -> None:
        self.assertEqual(
            self.run_delegate("claude", "--cwd", str(self.root / "README.md"), cwd=self.tmp),
            (2, {"error": "not_found"}),
        )

    def test_runtime_is_required_and_validated(self) -> None:
        for args in ([], ["--runtime", "gemini"]):
            with self.subTest(args=args):
                result = subprocess.run(
                    [sys.executable, str(self.script), "delegate", *args],
                    cwd=str(self.root), env=isolated_env({"HOME": str(self.home)}),
                    capture_output=True, text=True, timeout=30,
                )
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertIn("--runtime", result.stderr)


class HelperTests(TempProjectCase):
    def setUp(self) -> None:
        super().setUp()
        self.module = load_module(SCRIPT, "task_bootstrap_under_test")

    def test_fixture_isolated_from_global_git_config(self) -> None:
        # Plant a global config that sets the option; GIT_ENV must keep it from reaching the fixture repo.
        (self.home / ".gitconfig").write_text("[core]\n\texcludesFile = /nonexistent/ignore\n", encoding="utf-8")
        command = ["git", "-C", str(self.root), "config", "--get", "core.excludesFile"]
        env = isolated_env({"HOME": str(self.home)})
        isolated = subprocess.run(command, env=env, capture_output=True, text=True)
        self.assertNotEqual(isolated.returncode, 0, isolated.stdout)
        # Without the isolation the same planted file is visible, so the check above can actually fail.
        leaky = {k: v for k, v in env.items() if k != "GIT_CONFIG_GLOBAL"}
        planted = subprocess.run(command, env=leaky, capture_output=True, text=True)
        self.assertEqual(planted.returncode, 0)
        self.assertEqual(planted.stdout.strip(), "/nonexistent/ignore")

    def test_make_project_shape(self) -> None:
        project = self.project
        self.assertEqual(project.tmp, project.tmp.resolve())
        self.assertEqual(git_out(project.origin, "rev-parse", "--is-bare-repository"), "true")
        self.assertEqual(git_out(project.main, "rev-parse", "--show-toplevel"), str(project.main))
        self.assertEqual(git_out(project.main, "symbolic-ref", "--short", "HEAD"), "main")
        self.assertEqual(git_out(project.main, "symbolic-ref", "refs/remotes/origin/HEAD"), "refs/remotes/origin/main")
        self.assertEqual(git_out(project.main, "remote", "get-url", "origin"), project.origin.as_uri())
        self.assertEqual(git_out(project.main, "status", "--porcelain"), "")
        head = git_out(project.main, "rev-parse", "HEAD")
        self.assertEqual(git_out(project.main, "rev-parse", "origin/main"), head)
        self.assertEqual(git_out(project.origin, "rev-parse", "refs/heads/main"), head)
        self.assertEqual(git_out(project.main, "config", "branch.main.remote"), "origin")

    def test_fixture_environment_never_uses_the_real_home(self) -> None:
        # Every subprocess environment in this file comes from isolated_env, so this is the one place to check it.
        self.assertEqual(isolated_env()["HOME"], _scratch_home())
        self.assertNotEqual(Path(isolated_env()["HOME"]).resolve(), Path(os.path.expanduser("~")).resolve())
        self.assertEqual(isolated_env({"HOME": "/x"})["HOME"], "/x")
        self.assertEqual({k for k in isolated_env() if k.startswith("GIT_")} - set(GIT_ENV), set())

    def test_fixture_environment_drops_inherited_git_and_host_settings(self) -> None:
        leaking = {"GIT_DIR": "/x", "GIT_WORK_TREE": "/y", "TASK_BOOTSTRAP_WORKTREES_ROOT": "/z"}
        with mock.patch.dict(os.environ, leaking):
            env = isolated_env()
        for name in leaking:
            self.assertNotIn(name, env)

    def test_user_level_roots_match_session_start(self) -> None:
        mine = self.module
        theirs = load_module(SESSION_START_SCRIPT, "session_start_handoffs_for_comparison")
        for home in (Path("/h"), self.home, Path("/")):
            with self.subTest(home=str(home)):
                self.assertEqual(mine.user_level_roots(home), theirs.user_level_roots(home))
        self.assertEqual(mine.user_level_roots(Path("/h")), [
            Path("/h/.claude/skills"), Path("/h/.codex/skills"), Path("/h/.omp/agent/skills"),
            Path("/h/.claude/plugins"), Path("/h/.codex/plugins"),
        ])

    def test_self_skill_sits_next_to_scripts_dir(self) -> None:
        self.assertEqual(self.module.SELF_SKILL, SCRIPT.resolve().parent.parent / "SKILL.md")

    def test_inherited_git_dir_is_ignored(self) -> None:
        other = self.tmp / "other"
        other.mkdir()
        run_git(other, "init", "-q", "-b", "main")
        leaking = {**isolated_env(), "GIT_DIR": str(other / ".git"), "GIT_WORK_TREE": str(other)}
        # Guard: left alone, the inherited variables really do make git answer for the other repository.
        unscrubbed = subprocess.run(
            ["git", "-C", str(self.root), "rev-parse", "--show-toplevel"],
            env=leaking, capture_output=True, text=True,
        )
        self.assertEqual(Path(unscrubbed.stdout.strip()).resolve(), other.resolve())
        with mock.patch.dict(os.environ, leaking, clear=True):
            result = self.module.git(["rev-parse", "--show-toplevel"], cwd=self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(Path(result.stdout.strip()).resolve(), self.root)

    def test_git_environment_keeps_config_and_sets_non_interactive(self) -> None:
        leaking = {name: "/x" for name in (
            "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
            "GIT_COMMON_DIR", "GIT_PREFIX", "GIT_NAMESPACE", "GIT_CEILING_DIRECTORIES",
        )}
        inherited = {**leaking, **GIT_ENV, "GIT_OPTIONAL_LOCKS": "1", "GIT_TERMINAL_PROMPT": "1"}
        with mock.patch.dict(os.environ, inherited):
            env = self.module._git_environment()
        for name in leaking:
            self.assertNotIn(name, env)
        self.assertEqual(env["GIT_CONFIG_GLOBAL"], os.devnull)
        self.assertEqual(env["GIT_CONFIG_NOSYSTEM"], "1")
        self.assertEqual(env["GIT_OPTIONAL_LOCKS"], "0")
        self.assertEqual(env["GIT_TERMINAL_PROMPT"], "0")

    def test_git_passes_timeout_and_returns_none_on_failure(self) -> None:
        module = self.module
        completed = subprocess.CompletedProcess([], 0, "", "")
        with mock.patch.object(module.subprocess, "run", return_value=completed) as run:
            self.assertIs(module.git(["status"], self.root), completed)
            self.assertEqual(run.call_args.kwargs["timeout"], module.GIT_TIMEOUT_SECONDS)
            module.git(["fetch"], self.root, timeout=module.NETWORK_TIMEOUT_SECONDS)
            self.assertEqual(run.call_args.kwargs["timeout"], module.NETWORK_TIMEOUT_SECONDS)
            self.assertNotIn("shell", run.call_args.kwargs)
        self.assertEqual((module.GIT_TIMEOUT_SECONDS, module.NETWORK_TIMEOUT_SECONDS), (10, 60))
        for failure in (subprocess.TimeoutExpired("git", 1), FileNotFoundError("git")):
            with self.subTest(failure=type(failure).__name__):
                with mock.patch.object(module.subprocess, "run", side_effect=failure):
                    self.assertIsNone(module.git(["status"], self.root))

    def test_git_returns_none_when_git_is_missing(self) -> None:
        empty_bin = self.tmp / "empty-bin"
        empty_bin.mkdir()
        with mock.patch.dict(os.environ, {"PATH": str(empty_bin)}):
            self.assertIsNone(self.module.git(["status"], self.root))

    def test_emit_prints_utf8_json_and_returns_the_code(self) -> None:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            self.assertEqual(self.module.emit({"task": "修 login", "n": 1}), 0)
            self.assertEqual(self.module.emit({"error": "x"}, 3), 3)
        first, second = buffer.getvalue().splitlines()
        self.assertEqual(first, '{"task": "修 login", "n": 1}')
        self.assertEqual(json.loads(second), {"error": "x"})


PLAN_KEYS = {
    "mode", "task", "source", "asset_source", "remote", "default_branch", "base_ref", "branch", "slug", "target",
    "worktrees_root", "commands", "copies", "skipped_copies", "symlink", "executed",
}


class CreateCase(TempProjectCase):
    """What the plan tests of every `create` mode share: running the CLI, and proving a dry run changed nothing."""

    def setUp(self) -> None:
        super().setUp()
        self.worktrees = self.tmp / "worktrees"

    def plan(self, *args: str, branch: str = "feat/x", cwd: Path | None = None) -> dict:
        code, out = run_create(self.project, f"--branch={branch}", *args, cwd=cwd)
        self.assertEqual(code, 0, out)
        return out

    def refusal(self, *args: str, expect: str, branch: str = "feat/x", cwd: Path | None = None) -> dict:
        code, out = run_create(self.project, f"--branch={branch}", *args, cwd=cwd)
        self.assertEqual((code, out.get("error")), (3, expect), out)
        return out

    def snapshot(self) -> dict:
        return {
            "refs": git_out(self.root, "for-each-ref"),
            "worktrees": git_out(self.root, "worktree", "list"),
            "head": git_out(self.root, "rev-parse", "HEAD"),
            # Includes .git, so a fetch (FETCH_HEAD, new refs) would show up here too.
            "paths": sorted(str(path) for path in self.tmp.rglob("*")),
        }

    def unrelated_repository(self) -> Path:
        """A second clone of the same remote: it looks alike, but it has a git directory of its own."""
        other = self.tmp / "other-clone"
        run_git(self.tmp, "clone", "-q", self.project.origin.as_uri(), str(other))
        return other


class CreateMainPlanTests(CreateCase):
    """`create` in main mode without --execute: the shared checks and the plan they lead to."""

    def setUp(self) -> None:
        super().setUp()
        self.module = load_module(SCRIPT, "task_bootstrap_create_under_test")

    def rename_default_branch(self, name: str) -> None:
        """Rename main to `name` in the remote and in the main checkout, so the remote has no `main` any more."""
        run_git(self.root, "push", "-q", "origin", f"main:{name}")
        # The remote refuses to delete the branch its HEAD points to.
        run_git(self.project.origin, "symbolic-ref", "HEAD", f"refs/heads/{name}")
        run_git(self.project.origin, "update-ref", "-d", "refs/heads/main")
        run_git(self.root, "branch", "-m", "main", name)

    def test_main_plan_shape(self) -> None:
        out = self.plan()
        target = os.path.realpath(self.worktrees / "proj" / "feat-x")
        self.assertEqual(set(out), PLAN_KEYS)
        self.assertEqual(
            (out["mode"], out["default_branch"], out["base_ref"], out["slug"], out["branch"], out["remote"]),
            ("main", "main", "origin/main", "feat-x", "feat/x", "origin"),
        )
        self.assertEqual(os.path.realpath(out["target"]), target)
        self.assertEqual(out["target"], target)
        self.assertEqual(out["worktrees_root"], os.path.realpath(self.worktrees))
        self.assertEqual((out["source"], out["asset_source"]), (str(self.root), str(self.root)))
        self.assertIs(out["executed"], False)
        self.assertEqual((out["copies"], out["skipped_copies"], out["symlink"], out["task"]), ([], [], None, None))
        base = ["git", "-C", str(self.root)]
        self.assertEqual(out["commands"], [
            [*base, "fetch", "origin"],
            [*base, "pull", "--ff-only", "origin", "main"],
            # Fully qualified, while base_ref above stays the display form.
            [*base, "worktree", "add", "--no-track", "-b", "feat/x", target, "refs/remotes/origin/main"],
        ])

    def test_dry_run_changes_nothing(self) -> None:
        before = self.snapshot()
        self.plan()
        self.assertEqual(self.snapshot(), before)
        self.assertFalse(self.worktrees.exists())

    def test_default_source_is_main_checkout_from_linked_worktree(self) -> None:
        linked = self.tmp / "linked"
        run_git(self.root, "worktree", "add", "-q", "-b", "other", str(linked))
        expected = os.path.realpath(self.worktrees / "proj" / "feat-x")
        # Once as the process cwd and once through --cwd; the linked worktree sits on `other`, so it cannot be
        # mistaken for a source that passes the branch check.
        for out in (self.plan(cwd=linked), self.plan("--cwd", str(linked), cwd=self.tmp)):
            self.assertEqual((out["source"], out["asset_source"]), (str(self.root), str(self.root)))
            self.assertEqual((out["target"], out["worktrees_root"]), (expected, os.path.realpath(self.worktrees)))
            self.assertEqual(out["commands"][0][:3], ["git", "-C", str(self.root)])

    def test_source_option_overrides_source_only(self) -> None:
        # Free `main` so a linked worktree can hold it while the main checkout (the cwd) sits on another branch.
        run_git(self.root, "checkout", "-q", "-b", "work")
        linked = self.tmp / "linked"
        run_git(self.root, "worktree", "add", "-q", str(linked), "main")
        out = self.plan("--source", str(linked))
        self.assertEqual(out["source"], str(linked))
        self.assertEqual(out["asset_source"], str(self.root))
        self.assertEqual(out["target"], os.path.realpath(self.worktrees / "proj" / "feat-x"))
        self.assertEqual(out["worktrees_root"], os.path.realpath(self.worktrees))
        self.assertTrue(all(command[:3] == ["git", "-C", str(linked)] for command in out["commands"]))
        # Without --source the main checkout is the source, and it is on `work`.
        self.assertEqual(self.refusal(expect="source_branch_mismatch")["current"], "work")

    def test_unrelated_repo_as_source_refuses_in_every_mode(self) -> None:
        other = self.unrelated_repository()
        for mode in ("main", "baseline", "task"):
            with self.subTest(mode=mode):
                out = self.refusal("--mode", mode, "--source", str(other), expect="source_wrong_repo")
                self.assertEqual((out["role"], out["path"]), ("source", str(other)))
        # Called from inside the other repository, that one is the main checkout, and this project is the foreigner.
        other_cwd = self.refusal("--asset-source", str(self.root), cwd=other, expect="source_wrong_repo")
        self.assertEqual((other_cwd["role"], other_cwd["path"]), ("asset_source", str(self.root)))
        self.assertFalse(self.worktrees.exists())

    def test_unrelated_repo_as_asset_source_refuses(self) -> None:
        other = self.unrelated_repository()
        out = self.refusal("--asset-source", str(other), expect="source_wrong_repo")
        self.assertEqual((out["role"], out["path"]), ("asset_source", str(other)))
        # A linked worktree of this repository is a fine asset source.
        linked = self.tmp / "linked"
        run_git(self.root, "worktree", "add", "-q", "-b", "other", str(linked))
        self.assertEqual(self.plan("--asset-source", str(linked))["asset_source"], str(linked))

    def test_untracked_files_do_not_make_source_dirty(self) -> None:
        (self.root / ".env").write_text("TOKEN=1\n", encoding="utf-8")
        self.assertEqual(self.plan()["source"], str(self.root))

    def test_modified_tracked_file_refuses_source_dirty(self) -> None:
        readme = self.root / "README.md"
        readme.write_text("changed\n", encoding="utf-8")
        out = self.refusal(expect="source_dirty")
        self.assertEqual((out["entries"], out["changes"]), (1, [" M README.md"]))
        run_git(self.root, "checkout", "-q", "--", "README.md")
        self.plan()
        # A staged new file is a change too, not just an edit of a tracked one.
        (self.root / "new.txt").write_text("x\n", encoding="utf-8")
        run_git(self.root, "add", "new.txt")
        self.assertEqual(self.refusal(expect="source_dirty")["changes"], ["A  new.txt"])

    def test_source_on_other_branch_refuses(self) -> None:
        run_git(self.root, "checkout", "-q", "-b", "other")
        out = self.refusal(expect="source_branch_mismatch")
        self.assertEqual((out["current"], out["expected"], out["source"]), ("other", "main", str(self.root)))

    def test_detached_head_refuses(self) -> None:
        run_git(self.root, "checkout", "-q", "--detach")
        out = self.refusal(expect="source_branch_mismatch")
        self.assertEqual((out["current"], out["expected"]), (None, "main"))

    def test_default_branch_from_origin_head(self) -> None:
        # `main` still exists on the remote, so asking the remote (main/master) would pick the wrong branch here.
        run_git(self.root, "checkout", "-q", "-b", "trunk")
        run_git(self.root, "push", "-q", "origin", "trunk")
        run_git(self.root, "remote", "set-head", "origin", "trunk")
        # With this branch around, `symbolic-ref --short` would print "remotes/origin/trunk", and the short name
        # "origin/trunk" would name this local branch instead of the remote-tracking ref.
        lookalike = git_out(self.root, "commit-tree", "HEAD^{tree}", "-p", "HEAD", "-m", "local look-alike")
        run_git(self.root, "branch", "origin/trunk", lookalike)
        out = self.plan()
        self.assertEqual((out["default_branch"], out["base_ref"]), ("trunk", "origin/trunk"))
        self.assertEqual(out["commands"][1][3:], ["pull", "--ff-only", "origin", "trunk"])
        start_point = out["commands"][2][-1]
        self.assertEqual(start_point, "refs/remotes/origin/trunk")
        # Guard: the short name really does pick the local look-alike, and the printed start point does not.
        self.assertEqual(git_out(self.root, "rev-parse", "origin/trunk"), lookalike)
        self.assertEqual(git_out(self.root, "rev-parse", start_point), git_out(self.root, "rev-parse", "HEAD"))

    def test_default_branch_from_ls_remote_when_head_missing(self) -> None:
        run_git(self.root, "remote", "set-head", "origin", "-d")
        self.assertNotEqual(
            run_git(self.root, "symbolic-ref", "-q", "refs/remotes/origin/HEAD", check=False).returncode, 0
        )
        self.assertEqual(self.plan()["default_branch"], "main")
        # ls-remote patterns match the tail of a ref name, so `ls-remote origin main master` also returns
        # feature/main. Only `master` is a real default-branch candidate here.
        self.rename_default_branch("master")
        run_git(self.root, "push", "-q", "origin", "master:refs/heads/feature/main")
        self.assertEqual(self.plan()["default_branch"], "master")

    def test_default_branch_unknown_when_main_and_master_both_exist(self) -> None:
        run_git(self.root, "push", "-q", "origin", "main:master")
        run_git(self.root, "remote", "set-head", "origin", "-d")
        out = self.refusal(expect="default_branch_unknown")
        self.assertEqual(out["found"], ["main", "master"])

    def test_default_branch_override(self) -> None:
        self.rename_default_branch("trunk")
        run_git(self.root, "remote", "set-head", "origin", "-d")
        self.assertEqual(self.refusal(expect="default_branch_unknown")["found"], [])
        out = self.plan("--default-branch", "trunk")
        self.assertEqual((out["default_branch"], out["base_ref"]), ("trunk", "origin/trunk"))
        # The override still has to be a branch name.
        invalid = self.refusal("--default-branch=bad..name", expect="branch_invalid")
        self.assertEqual((invalid["branch"], invalid["option"]), ("bad..name", "--default-branch"))

    def test_remote_url_allowlist(self) -> None:
        allowed = self.module.remote_url_allowed
        for url in ("https://h/o/r.git", "ssh://git@h/o/r.git", "git://h/r.git", "file:///tmp/r.git", "git@h:o/r.git",
                    "alias:o/r.git"):
            with self.subTest(allowed=url):
                self.assertTrue(allowed(url))
        for url in ("http://h/r.git", "ext::sh -c id", "fd::3", "/tmp/r.git", "-oProxyCommand=x", ""):
            with self.subTest(rejected=url):
                self.assertFalse(allowed(url))

    def test_remote_name_must_exist(self) -> None:
        # "-x" has a guard of its own: git would read it as an option.
        for remote in ("nope", "-x"):
            with self.subTest(remote=remote):
                self.assertEqual(self.refusal(f"--remote={remote}", expect="remote_invalid")["remote"], remote)

    def test_rejected_remote_url_refuses_before_any_network(self) -> None:
        marker = self.tmp / "helper-ran"
        allow = {"GIT_ALLOW_PROTOCOL": "ext"}
        # Without origin/HEAD the default branch would be found through ls-remote, which would start the helper.
        run_git(self.root, "remote", "set-head", "origin", "-d")
        run_git(self.root, "remote", "set-url", "origin", f"ext::touch {marker}")
        # Guard: with the protocol enabled, git really does run the helper, so a missing marker below means something.
        subprocess.run(
            ["git", "-C", str(self.root), "ls-remote", "origin"], env=isolated_env(allow), capture_output=True,
            timeout=30,
        )
        self.assertTrue(marker.exists())
        marker.unlink()
        code, out = run_script("create", "--branch=feat/x", cwd=self.root, env={"HOME": str(self.home), **allow})
        self.assertEqual((code, out), (3, {"error": "remote_url_rejected", "remote": "origin"}))
        self.assertFalse(marker.exists())
        # The plain form of the same helper URL, without the marker.
        run_git(self.root, "remote", "set-url", "origin", "ext::sh -c true")
        self.refusal(expect="remote_url_rejected")
        # The URL may carry credentials, so it is never printed.
        run_git(self.root, "remote", "set-url", "origin", "ftp://user:s3cret@h/r.git")
        code, out = run_create(self.project, "--branch=feat/x")
        self.assertEqual((code, out["error"]), (3, "remote_url_rejected"))
        self.assertNotIn("s3cret", json.dumps(out))

    def test_url_is_judged_after_insteadof_rewriting(self) -> None:
        # The configured URL passes the allowlist as an scp-style alias, but git would fetch from the rewritten one.
        run_git(self.root, "config", "url.http://rewritten/.insteadOf", "alias:")
        run_git(self.root, "remote", "set-url", "origin", "alias:o/r.git")
        self.assertTrue(self.module.remote_url_allowed("alias:o/r.git"))
        self.refusal(expect="remote_url_rejected")

    def test_branch_validation(self) -> None:
        # Gives `@{-1}` something to expand to; without it the name would simply be unknown.
        run_git(self.root, "checkout", "-q", "-b", "prev")
        run_git(self.root, "checkout", "-q", "main")
        self.assertEqual(git_out(self.root, "check-ref-format", "--branch", "@{-1}"), "prev")
        for name in ("bad..name", "-x", "a b", "x.lock", "@{-1}"):
            with self.subTest(branch=name):
                self.assertEqual(self.refusal(branch=name, expect="branch_invalid")["branch"], name)

    def test_slug_rules(self) -> None:
        out = self.plan(branch="Fix/Login")
        self.assertEqual((out["branch"], out["slug"]), ("Fix/Login", "fix-login"))
        self.assertEqual(out["target"], os.path.realpath(self.worktrees / "proj" / "fix-login"))
        for slug in ("../x", ".", "Upper"):
            with self.subTest(slug=slug):
                self.assertEqual(self.refusal(f"--slug={slug}", expect="slug_invalid")["slug"], slug)
        # A branch name that cannot become a slug is not cleaned up; the user supplies the slug instead.
        self.assertEqual(self.refusal(branch="feat/é", expect="slug_invalid")["slug"], "feat-é")
        out = self.plan("--slug", "feat-e", branch="feat/é")
        self.assertEqual((out["branch"], out["slug"]), ("feat/é", "feat-e"))

    def test_branch_exists_refuses(self) -> None:
        run_git(self.root, "branch", "feat/x")
        self.assertEqual(self.refusal(expect="branch_exists")["branch"], "feat/x")

    def test_target_exists_refuses(self) -> None:
        (self.worktrees / "proj" / "feat-x").mkdir(parents=True)
        out = self.refusal(expect="target_exists")
        self.assertEqual(out["target"], os.path.realpath(self.worktrees / "proj" / "feat-x"))

    def test_target_that_is_a_symlink_refuses(self) -> None:
        link = self.worktrees / "proj" / "feat-x"
        link.parent.mkdir(parents=True)
        link.symlink_to(link.parent / "missing")
        # Dangling, but still something `worktree add` would trip over.
        self.refusal(expect="target_exists")
        link.unlink()
        link.symlink_to(self.tmp / "elsewhere")
        self.assertEqual(self.refusal(expect="target_outside_root")["worktrees_root"], os.path.realpath(self.worktrees))

    def test_symlinked_worktrees_root_refuses(self) -> None:
        elsewhere = self.tmp / "elsewhere"
        elsewhere.mkdir()
        self.worktrees.symlink_to(elsewhere)
        self.assertEqual(self.refusal(expect="parent_symlink")["path"], str(self.worktrees))
        # An explicit root gets the same treatment as the default one.
        explicit = self.refusal(f"--worktrees-root={self.worktrees}", expect="parent_symlink")
        self.assertEqual(explicit["path"], str(self.worktrees))
        self.assertEqual(list(elsewhere.iterdir()), [])

    def test_symlinked_repo_dir_refuses(self) -> None:
        elsewhere = self.tmp / "elsewhere"
        elsewhere.mkdir()
        self.worktrees.mkdir()
        (self.worktrees / "proj").symlink_to(elsewhere)
        self.assertEqual(self.refusal(expect="parent_symlink")["path"], str(self.worktrees / "proj"))
        self.assertEqual(list(elsewhere.iterdir()), [])

    def test_worktrees_root_precedence(self) -> None:
        from_env, from_flag = self.tmp / "from-env", self.tmp / "from-flag"
        env = {"HOME": str(self.home), "TASK_BOOTSTRAP_WORKTREES_ROOT": str(from_env)}
        code, out = run_script("create", "--branch=feat/x", cwd=self.root, env=env)
        self.assertEqual(code, 0)
        self.assertEqual((out["target"], out["worktrees_root"]), (str(from_env / "proj" / "feat-x"), str(from_env)))
        code, out = run_script("create", "--branch=feat/x", f"--worktrees-root={from_flag}", cwd=self.root, env=env)
        self.assertEqual((code, out["target"]), (0, str(from_flag / "proj" / "feat-x")))
        # An empty variable counts as unset.
        unset = {**env, "TASK_BOOTSTRAP_WORKTREES_ROOT": ""}
        code, out = run_script("create", "--branch=feat/x", cwd=self.root, env=unset)
        self.assertEqual((code, out["target"]), (0, os.path.realpath(self.worktrees / "proj" / "feat-x")))

    def test_relative_paths_resolve_against_cwd_option(self) -> None:
        out = self.plan("--cwd", str(self.root), "--worktrees-root", "rel-root", "--source", ".", cwd=self.tmp)
        self.assertEqual(out["source"], str(self.root))
        self.assertEqual(out["target"], str(self.root / "rel-root" / "proj" / "feat-x"))

    def test_task_text_echoed_verbatim(self) -> None:
        self.assertEqual(self.plan("--task", "fix login")["task"], "fix login")
        # Spaces at the ends, CJK, quotes and shell metacharacters all have to survive unchanged.
        text = ' fix login 修 "bug" \\ $HOME `x` '
        self.assertEqual(self.plan("--task", text)["task"], text)

    def test_outside_a_repository_refuses(self) -> None:
        plain = self.tmp / "plain"
        plain.mkdir()
        code, out = run_script("create", "--branch=feat/x", cwd=plain, env={"HOME": str(self.home)})
        self.assertEqual((code, out["error"]), (3, "source_not_git"))

    def test_bare_repository_cannot_be_the_source(self) -> None:
        # The first entry of a bare repository's worktree list is the bare repository itself.
        linked = self.tmp / "from-bare"
        run_git(self.project.origin, "worktree", "add", "-q", str(linked), "main")
        code, out = run_script("create", "--branch=feat/x", cwd=linked, env={"HOME": str(self.home)})
        self.assertEqual((code, out["error"]), (3, "source_not_git"))

    def test_missing_directories_exit_2(self) -> None:
        missing = self.tmp / "nope"
        for option in ("--cwd", "--source", "--asset-source"):
            with self.subTest(option=option):
                # The process cwd is somewhere that exists, so only the option can be what is wrong.
                code, out = run_create(self.project, "--branch=feat/x", option, str(missing))
                self.assertEqual((code, out), (2, {"error": "not_found", "path": str(missing)}))

    def test_source_that_is_not_a_repository_refuses(self) -> None:
        plain = self.tmp / "plain"
        plain.mkdir()
        self.assertEqual(self.refusal("--source", str(plain), expect="source_not_git")["path"], str(plain))

    def test_unbuilt_options_are_refused_not_ignored(self) -> None:
        before = self.snapshot()
        for mode in ("main", "baseline", "task"):
            with self.subTest(mode=mode):
                self.refusal("--mode", mode, "--execute", expect="option_unsupported")
        self.assertEqual(self.snapshot(), before)

    def test_usage_errors_exit_2(self) -> None:
        for args in ([], ["--branch=feat/x", "--mode", "elsewhere"]):
            with self.subTest(args=args):
                result = subprocess.run(
                    [sys.executable, str(SCRIPT), "create", *args], cwd=str(self.root),
                    env=isolated_env({"HOME": str(self.home)}), capture_output=True, text=True, timeout=30,
                )
                self.assertEqual((result.returncode, result.stdout), (2, ""))
                self.assertRegex(result.stderr, "--branch|--mode")


class CreateOtherModesTests(CreateCase):
    """`create` in baseline and task mode without --execute."""

    def setUp(self) -> None:
        super().setUp()
        # The remote's release branch is one commit ahead of main, so a worktree on it can be told from one on main.
        self.release_tip = git_out(self.root, "commit-tree", "HEAD^{tree}", "-p", "HEAD", "-m", "release work")
        run_git(self.root, "push", "-q", "origin", f"{self.release_tip}:refs/heads/release/1.0")

    def linked_worktree_on(self, branch: str) -> Path:
        """A linked worktree stopped on a new `branch` that is one commit ahead of main."""
        linked = self.tmp / "linked"
        run_git(self.root, "worktree", "add", "-q", "-b", branch, str(linked))
        run_git(linked, "commit", "-q", "--allow-empty", "-m", "work on the branch")
        return linked

    def run_commands(self, commands: list[list[str]]) -> None:
        """Run the commands a plan printed, to see that git does what the plan says it does."""
        for command in commands:
            result = subprocess.run(
                command, env=isolated_env({"HOME": str(self.home)}), capture_output=True, text=True, timeout=30
            )
            self.assertEqual(result.returncode, 0, (command, result.stderr))

    def test_baseline_plan(self) -> None:
        before = self.snapshot()
        out = self.plan("--mode", "baseline", branch="release/1.0")
        target = os.path.realpath(self.worktrees / "proj" / "release-1.0")
        self.assertEqual(set(out), PLAN_KEYS)
        self.assertEqual(
            (out["mode"], out["default_branch"], out["base_ref"], out["branch"], out["slug"], out["remote"]),
            ("baseline", None, "origin/release/1.0", "release/1.0", "release-1.0", "origin"),
        )
        self.assertEqual(out["target"], target)
        self.assertEqual((out["source"], out["asset_source"]), (str(self.root), str(self.root)))
        self.assertEqual((out["copies"], out["skipped_copies"], out["symlink"], out["executed"]), ([], [], None, False))
        base = ["git", "-C", str(self.root)]
        self.assertEqual(out["commands"], [
            [*base, "fetch", "origin", "release/1.0"],
            # --track is the point of a baseline; the start point is fully qualified like main mode's.
            [*base, "worktree", "add", "--track", "-b", "release/1.0", target, "refs/remotes/origin/release/1.0"],
        ])
        self.assertEqual(self.snapshot(), before)
        self.assertFalse(self.worktrees.exists())

    def test_baseline_commands_create_a_tracking_worktree(self) -> None:
        # A local branch with the remote-tracking branch's short name: written as "origin/release/1.0", the start
        # point would resolve to this one instead.
        run_git(self.root, "branch", "origin/release/1.0", "main")
        out = self.plan("--mode", "baseline", branch="release/1.0")
        self.run_commands(out["commands"])
        target = Path(out["target"])
        self.assertEqual(git_out(target, "symbolic-ref", "--short", "HEAD"), "release/1.0")
        self.assertEqual(git_out(target, "rev-parse", "HEAD"), self.release_tip)
        self.assertEqual(git_out(self.root, "config", "branch.release/1.0.remote"), "origin")
        self.assertEqual(git_out(self.root, "config", "branch.release/1.0.merge"), "refs/heads/release/1.0")

    def test_baseline_branch_missing_on_remote_refuses(self) -> None:
        out = self.refusal("--mode", "baseline", branch="release/9.9", expect="branch_missing_on_remote")
        self.assertEqual((out["remote"], out["branch"]), ("origin", "release/9.9"))

    def test_baseline_branch_must_match_exactly(self) -> None:
        run_git(self.project.origin, "update-ref", "-d", "refs/heads/release/1.0")
        run_git(self.root, "push", "-q", "origin", f"{self.release_tip}:refs/heads/x/release/1.0")
        # Guard: ls-remote matches the tail of a ref name, so it lists the other branch for this pattern.
        self.assertIn("refs/heads/x/release/1.0", git_out(self.root, "ls-remote", "--heads", "origin", "release/1.0"))
        self.refusal("--mode", "baseline", branch="release/1.0", expect="branch_missing_on_remote")

    def test_baseline_ls_remote_failure_is_not_a_missing_branch(self) -> None:
        run_git(self.root, "remote", "set-url", "origin", "file:///nonexistent/task-bootstrap/none.git")
        out = self.refusal("--mode", "baseline", branch="release/1.0", expect="git_failed")
        self.assertEqual(out["command"], "ls-remote")
        # What git says about a failed remote names its URL, which may carry credentials.
        self.assertNotIn("nonexistent", json.dumps(out))

    def test_baseline_local_branch_exists_refuses(self) -> None:
        run_git(self.root, "branch", "release/1.0", "main")
        out = self.refusal("--mode", "baseline", branch="release/1.0", expect="branch_exists")
        self.assertEqual(out["branch"], "release/1.0")

    def test_baseline_ignores_dirty_source(self) -> None:
        (self.root / "README.md").write_text("changed\n", encoding="utf-8")
        (self.root / "new.txt").write_text("x\n", encoding="utf-8")
        run_git(self.root, "add", "new.txt")
        # Guard: main mode really does see this source as dirty.
        self.refusal(expect="source_dirty")
        self.assertEqual(self.plan("--mode", "baseline", branch="release/1.0")["mode"], "baseline")

    def test_baseline_needs_neither_default_branch_nor_source_branch(self) -> None:
        run_git(self.root, "push", "-q", "origin", "main:master")
        run_git(self.root, "remote", "set-head", "origin", "-d")
        # Guard: with both main and master on the remote and no origin/HEAD, main mode cannot pick a default.
        self.refusal(expect="default_branch_unknown")
        run_git(self.root, "checkout", "-q", "-b", "other")
        self.assertIsNone(self.plan("--mode", "baseline", branch="release/1.0")["default_branch"])
        run_git(self.root, "checkout", "-q", "--detach")
        self.assertEqual(self.plan("--mode", "baseline", branch="release/1.0")["base_ref"], "origin/release/1.0")

    def test_baseline_checks_the_remote_like_main_mode(self) -> None:
        self.assertEqual(
            self.refusal("--mode", "baseline", "--remote=nope", branch="release/1.0", expect="remote_invalid")["remote"],
            "nope",
        )
        marker = self.tmp / "helper-ran"
        allow = {"GIT_ALLOW_PROTOCOL": "ext"}
        run_git(self.root, "remote", "set-url", "origin", f"ext::touch {marker}")
        # Guard: with the protocol enabled, git really does run the helper, so a missing marker below means something.
        subprocess.run(
            ["git", "-C", str(self.root), "ls-remote", "origin"], env=isolated_env(allow), capture_output=True,
            timeout=30,
        )
        self.assertTrue(marker.exists())
        marker.unlink()
        code, out = run_script(
            "create", "--mode", "baseline", "--branch=release/1.0", cwd=self.root,
            env={"HOME": str(self.home), **allow},
        )
        self.assertEqual((code, out), (3, {"error": "remote_url_rejected", "remote": "origin"}))
        self.assertFalse(marker.exists())

    def test_task_plan(self) -> None:
        linked = self.linked_worktree_on("feat/a")
        before = self.snapshot()
        out = self.plan("--mode", "task", "--source", str(linked), "--base-ref", "feat/a", branch="feat/b")
        target = os.path.realpath(self.worktrees / "proj" / "feat-b")
        self.assertEqual(set(out), PLAN_KEYS)
        self.assertEqual(
            (out["mode"], out["default_branch"], out["base_ref"], out["branch"], out["slug"]),
            ("task", None, "feat/a", "feat/b", "feat-b"),
        )
        self.assertEqual(out["target"], target)
        self.assertEqual((out["source"], out["asset_source"]), (str(linked), str(self.root)))
        self.assertEqual((out["copies"], out["skipped_copies"], out["symlink"], out["executed"]), ([], [], None, False))
        # No fetch: task mode starts from what the source already has.
        self.assertEqual(out["commands"], [
            ["git", "-C", str(linked), "worktree", "add", "--no-track", "-b", "feat/b", target, "feat/a"],
        ])
        self.assertEqual(self.snapshot(), before)
        self.assertFalse(self.worktrees.exists())

    def test_task_commands_create_a_branch_without_upstream(self) -> None:
        # A remote-tracking start point is the case where git would set an upstream on its own.
        out = self.plan("--mode", "task", "--base-ref", "origin/main", branch="feat/b")
        self.run_commands(out["commands"])
        target = Path(out["target"])
        self.assertEqual(git_out(target, "symbolic-ref", "--short", "HEAD"), "feat/b")
        self.assertEqual(git_out(target, "rev-parse", "HEAD"), git_out(self.root, "rev-parse", "origin/main"))
        self.assertEqual(run_git(self.root, "config", "--get", "branch.feat/b.remote", check=False).returncode, 1)
        self.assertEqual(run_git(self.root, "config", "--get", "branch.feat/b.merge", check=False).returncode, 1)

    def test_task_requires_base_ref(self) -> None:
        for args in (("--mode", "task"), ("--mode", "task", "--base-ref=")):
            with self.subTest(args=args):
                self.refusal(*args, branch="feat/b", expect="base_ref_required")

    def test_task_base_ref_must_resolve(self) -> None:
        # "-x" would be read as an option, and a blob or a tree has no commit to start from.
        for ref in ("nope", "-x", "HEAD:README.md", "main^{tree}"):
            with self.subTest(base_ref=ref):
                out = self.refusal("--mode", "task", f"--base-ref={ref}", branch="feat/b", expect="base_ref_invalid")
                self.assertEqual(out["base_ref"], ref)

    def test_task_source_must_be_on_base_ref(self) -> None:
        linked = self.linked_worktree_on("feat/a")
        main_head, feature_head = git_out(self.root, "rev-parse", "HEAD"), git_out(linked, "rev-parse", "HEAD")
        self.assertNotEqual(main_head, feature_head)
        out = self.refusal("--mode", "task", "--base-ref", "feat/a", branch="feat/b", expect="base_ref_mismatch")
        self.assertEqual(
            (out["source"], out["base_ref"], out["current"], out["expected"]),
            (str(self.root), "feat/a", main_head, feature_head),
        )
        self.refusal(
            "--mode", "task", "--source", str(linked), "--base-ref", "main", branch="feat/b", expect="base_ref_mismatch"
        )
        # It is the commit that has to match, not the spelling: a SHA works, and so does a detached HEAD.
        run_git(linked, "checkout", "-q", "--detach")
        out = self.plan("--mode", "task", "--source", str(linked), "--base-ref", feature_head, branch="feat/b")
        self.assertEqual(out["commands"][0][-1], feature_head)

    def test_task_dirty_source_refuses(self) -> None:
        (self.root / "README.md").write_text("changed\n", encoding="utf-8")
        out = self.refusal("--mode", "task", "--base-ref", "main", branch="feat/b", expect="source_dirty")
        self.assertEqual((out["entries"], out["changes"]), (1, [" M README.md"]))

    def test_task_source_wrong_repo_refuses(self) -> None:
        other = self.unrelated_repository()
        out = self.refusal(
            "--mode", "task", "--source", str(other), "--base-ref", "main", branch="feat/b", expect="source_wrong_repo"
        )
        self.assertEqual((out["role"], out["path"]), ("source", str(other)))

    def test_task_mode_works_without_remote(self) -> None:
        marker = self.tmp / "helper-ran"
        allow = {"GIT_ALLOW_PROTOCOL": "ext"}
        run_git(self.root, "remote", "set-url", "origin", f"ext::touch {marker}")
        # Guard: with the protocol enabled, git really does run the helper, so a missing marker below means something.
        subprocess.run(
            ["git", "-C", str(self.root), "ls-remote", "origin"], env=isolated_env(allow), capture_output=True,
            timeout=30,
        )
        self.assertTrue(marker.exists())
        marker.unlink()
        # A remote that main mode would refuse (and that would run a command if it were contacted) is not looked at.
        code, out = run_script(
            "create", "--mode", "task", "--base-ref", "main", "--branch=feat/b", cwd=self.root,
            env={"HOME": str(self.home), **allow},
        )
        self.assertEqual(code, 0, out)
        self.assertFalse(marker.exists())
        run_git(self.root, "remote", "remove", "origin")
        self.assertEqual(git_out(self.root, "remote"), "")
        out = self.plan("--mode", "task", "--base-ref", "main", branch="feat/b")
        target = os.path.realpath(self.worktrees / "proj" / "feat-b")
        self.assertEqual((out["default_branch"], out["base_ref"]), (None, "main"))
        self.assertEqual(out["commands"], [
            ["git", "-C", str(self.root), "worktree", "add", "--no-track", "-b", "feat/b", target, "main"],
        ])

    def test_new_modes_validate_names(self) -> None:
        for args in (("--mode", "baseline"), ("--mode", "task", "--base-ref", "main")):
            with self.subTest(args=args):
                self.assertEqual(self.refusal(*args, branch="bad..name", expect="branch_invalid")["branch"], "bad..name")
                self.assertEqual(self.refusal(*args, "--slug=../x", expect="slug_invalid")["slug"], "../x")


class CreateHelperTests(unittest.TestCase):
    """The pure pieces of `create` called in-process: many inputs, no repository, no CLI run per input."""

    def setUp(self) -> None:
        self.module = load_module(SCRIPT, "task_bootstrap_create_helpers_under_test")
        # git() reads os.environ, so give it the same isolated environment the CLI tests use.
        patcher = mock.patch.dict(os.environ, isolated_env(), clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        # check-ref-format needs no repository.
        self.cwd = Path(temporary.name)

    def refusal_code(self, call, *args) -> str:
        with self.assertRaises(self.module.Refusal) as caught:
            call(*args)
        return caught.exception.code

    def test_remote_url_allowlist_edges(self) -> None:
        allowed = self.module.remote_url_allowed
        for url in ("https://h:8443/o/r", "ssh://git@h:22/o/r.git", "git@h:/abs/r.git", "file://localhost/r.git",
                    "user@h.example:o/r", "h:o"):
            with self.subTest(allowed=url):
                self.assertTrue(allowed(url))
        for url in (
            "ext::touch/x", "ftp://h/r.git", "HTTPS://h/r.git", "https://", "https:///r.git",
            "ssh://-oProxyCommand=x/r", "ssh://git@-h/r", "https://h/o r.git", " https://h/r.git", "https://h/r.git\n",
            "a/b:c", "h:", "h:two words", "-", "user@-h:r", "relative/path", "../r.git", "h:\x00", "[::1]:r.git",
        ):
            with self.subTest(rejected=url):
                self.assertFalse(allowed(url))

    def test_derive_and_validate_slug(self) -> None:
        derive, validate = self.module.derive_slug, self.module.validate_slug
        self.assertEqual(derive("Fix/Login"), "fix-login")
        self.assertEqual(derive("a/b/C"), "a-b-c")
        # lower() would turn the Kelvin sign into "k"; the name must be refused, not rewritten.
        self.assertEqual(derive("feat/\u212a"), "feat-\u212a")
        for slug in ("fix-login", "a", "0", "v1.2_x-y", "my.slug_1"):
            with self.subTest(valid=slug):
                self.assertEqual(validate(slug), slug)
        for slug in ("", ".", "..", "../x", "a/b", "Upper", "ok\n", "-x", ".hidden", "_x",
                     "feat-é","feat-\u212a", "a b"):
            with self.subTest(invalid=slug):
                self.assertEqual(self.refusal_code(validate, slug), "slug_invalid")

    def test_validate_branch_edges(self) -> None:
        validate = self.module.validate_branch
        for name in ("main", "feat/x", "Fix/Login", "release-1.2", "feat/é", "a.b"):
            with self.subTest(valid=name):
                self.assertEqual(validate(name, self.cwd), name)
        for name in ("", "-x", "--help", "bad..name", "a b", "x.lock", "@{-1}", "feat/x/", "a~b", "a:b", "HEAD",
                     "a\nb"):
            with self.subTest(invalid=name):
                self.assertEqual(self.refusal_code(validate, name, self.cwd), "branch_invalid")


if __name__ == "__main__":
    unittest.main()
