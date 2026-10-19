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


if __name__ == "__main__":
    unittest.main()
