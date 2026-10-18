"""Tests for session-start/scripts/handoffs.py: frontmatter parsing, assertions, and the check and list subcommands."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock


SOURCE_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = SOURCE_ROOT / "session-start" / "scripts" / "handoffs.py"
HANDOFF_SKILL = SOURCE_ROOT / "handoff" / "SKILL.md"

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


def load_module():
    """Import handoffs.py by path; it is a script, not a package member."""
    spec = importlib.util.spec_from_file_location("session_start_handoffs", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    # @dataclass resolves string annotations through sys.modules, so register before executing.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


handoffs = load_module()


def isolated_env(extra: dict | None = None) -> dict:
    """Environment for every git call and CLI run: no inherited GIT_* (a pre-commit hook sets GIT_DIR) plus GIT_ENV."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_ENV)
    env.update(extra or {})
    return env


def run_git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        env=isolated_env(),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=check,
    )


def make_repo(path: Path) -> Path:
    """Create a repo on branch main with one commit; handoff files stay out of git status via info/exclude."""
    path.mkdir(parents=True, exist_ok=True)
    run_git(path, "init", "-q", "-b", "main")
    exclude = path / ".git" / "info" / "exclude"
    exclude.parent.mkdir(parents=True, exist_ok=True)
    with exclude.open("a", encoding="utf-8") as handle:
        handle.write(".claude/handoffs/\n")
    (path / "README.md").write_text("fixture\n", encoding="utf-8")
    run_git(path, "add", "README.md")
    run_git(path, "commit", "-q", "-m", "init")
    return path


def write_handoff(dir: Path, name: str, *, frontmatter: str, body: str = "## 任務\nx\n") -> Path:  # noqa: A002
    # `dir` mirrors the plan's interface so keyword callers in later tasks keep working.
    dir.mkdir(parents=True, exist_ok=True)
    path = dir / name
    path.write_text(f"---\n{frontmatter.strip(chr(10))}\n---\n\n{body}", encoding="utf-8")
    return path


def run_cli(script: Path, *args: str, cwd: Path, env: dict | None = None) -> tuple[int, dict]:
    """Run the CLI in a subprocess; env entries are merged over the isolated git environment."""
    result = subprocess.run(
        [sys.executable, str(script), *args],
        cwd=str(cwd),
        env=isolated_env(env),
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
    )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise AssertionError(
            f"stdout is not JSON (exit {result.returncode}): {result.stdout!r}; stderr: {result.stderr!r}"
        ) from error
    return result.returncode, payload


# Mirrors the template in handoff/SKILL.md, including its trailing comments, colons inside values and CJK text.
TEMPLATE_FRONTMATTER = """\
branch: tom/post-profile-invite-later-copy   # 權威值，未 sanitize
worktree: /path/to/your-repo                   # 當前 worktree / repo 根
created: 2026-06-29T18:30:00+08:00
task: L10N upstream 條件式同步                # 一行任務標題
status: in-progress   # a | b
assertions:                                   # 機器可驗前提；無則省略整個 key
  - kind: expect_head
    repo: /r
    value: abc1234
  - kind: worktree_clean
    repo: /path/to/your-repo
"""
TEMPLATE_BODY = "## 任務\n（一行）\n\n## 下一步\n先跑測試\n"


def template_bytes(*, crlf: bool = False, bom: bool = False) -> bytes:
    text = f"---\n{TEMPLATE_FRONTMATTER}---\n\n{TEMPLATE_BODY}"
    if crlf:
        text = text.replace("\n", "\r\n")
    return (b"\xef\xbb\xbf" if bom else b"") + text.encode("utf-8")


class RepoTestCase(unittest.TestCase):
    """Throwaway repo plus an isolated process environment, so in-process git calls match the CLI runs."""

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.tmp = Path(temporary.name)
        patcher = mock.patch.dict(os.environ, isolated_env(), clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.repo = make_repo(self.tmp / "repo")
        self.handoff_dir = self.repo / ".claude" / "handoffs"

    def head(self) -> str:
        return run_git(self.repo, "rev-parse", "HEAD").stdout.strip()


class ParseTests(unittest.TestCase):
    def assert_template_fields(self, parsed) -> None:
        self.assertEqual(parsed.kind, "ok")
        self.assertEqual(parsed.fields["status"], "in-progress")
        self.assertEqual(parsed.fields["task"], "L10N upstream 條件式同步")
        self.assertEqual(parsed.fields["created"], "2026-06-29T18:30:00+08:00")
        self.assertEqual(parsed.fields["branch"], "tom/post-profile-invite-later-copy")
        self.assertEqual(len(parsed.assertions), 2)
        self.assertEqual(parsed.assertions[0], {"kind": "expect_head", "repo": "/r", "value": "abc1234"})
        self.assertEqual(parsed.assertions[1], {"kind": "worktree_clean", "repo": "/path/to/your-repo"})
        self.assertNotIn("assertions", parsed.fields)

    def test_parse_template_shape(self) -> None:
        raw = template_bytes()
        parsed = handoffs.parse_handoff(raw)
        self.assert_template_fields(parsed)
        self.assertEqual(raw[parsed.body_offset:].decode("utf-8"), parsed.body)
        self.assertTrue(parsed.body.lstrip().startswith("## 任務"))

    def test_parse_crlf_and_bom(self) -> None:
        raw = template_bytes(crlf=True, bom=True)
        parsed = handoffs.parse_handoff(raw)
        self.assert_template_fields(parsed)
        # body_offset indexes the original bytes (BOM, CRLF and multibyte text included) so a later rewrite can
        # keep the body byte-identical; the str body is newline-normalised.
        self.assertEqual(raw[parsed.body_offset:].decode("utf-8").replace("\r\n", "\n"), parsed.body)

    def test_parse_quotes_and_comments(self) -> None:
        raw = b"---\nstatus: 'blocked'\ntask: \"Fix: the # thing\"   # trailing\nnote: a#b c\nempty:\n---\nbody\n"
        parsed = handoffs.parse_handoff(raw)
        self.assertEqual(parsed.kind, "ok")
        self.assertEqual(parsed.fields["status"], "blocked")
        self.assertEqual(parsed.fields["task"], "Fix: the # thing")
        self.assertEqual(parsed.fields["note"], "a#b c")
        self.assertEqual(parsed.fields["empty"], "")

    def test_parse_inline_empty_assertions_is_ok(self) -> None:
        parsed = handoffs.parse_handoff(b"---\nstatus: blocked\nassertions: []\n---\n")
        self.assertEqual(parsed.kind, "ok")
        self.assertEqual(parsed.assertions, [])

    def test_parse_without_frontmatter_is_not_handoff(self) -> None:
        for raw in (b"# just a note\nstatus: in-progress\n", b"", b"\n---\nstatus: x\n---\n"):
            with self.subTest(raw=raw):
                self.assertEqual(handoffs.parse_handoff(raw).kind, "not_handoff")

    def test_parse_unterminated_frontmatter_is_not_handoff(self) -> None:
        self.assertEqual(handoffs.parse_handoff(b"---\nstatus: blocked\nno closing fence\n").kind, "not_handoff")

    def test_parse_without_status_is_not_handoff(self) -> None:
        self.assertEqual(handoffs.parse_handoff(b"---\ntask: x\nbranch: main\n---\n\nbody\n").kind, "not_handoff")

    def test_parse_nested_mapping_is_malformed(self) -> None:
        raw = "---\nstatus: blocked\nextra:\n  child: 1\n---\n\n## 任務\nx\n".encode("utf-8")
        parsed = handoffs.parse_handoff(raw)
        self.assertEqual(parsed.kind, "malformed")
        self.assertEqual(parsed.fields["status"], "blocked")
        self.assertEqual(parsed.assertions, [])
        self.assertIn("任務", handoffs.split_sections(parsed.body))

    def test_parse_other_unsupported_shapes_are_malformed(self) -> None:
        cases = {
            "block list value": "status: blocked\ntags:\n  - a\n  - b",
            "flow list value": "status: blocked\ntags: [a, b]",
            "flow mapping value": "status: blocked\nmeta: {a: 1}",
            "block scalar": "status: blocked\nnote: |\n  line one\n  line two",
            "duplicate key": "status: blocked\nstatus: in-progress",
            "line without a key": "status: blocked\njust some words",
            "assertion item without a key": "status: blocked\nassertions:\n  - plain",
            "assertion continuation without an item": "status: blocked\nassertions:\n    repo: /r",
            "nested value in an assertion": "status: blocked\nassertions:\n  - kind: expect_head\n    repo:\n      deep: 1",
            "duplicate key in an assertion": "status: blocked\nassertions:\n  - kind: a\n    kind: b",
            "assertions given a scalar": "status: blocked\nassertions: nope",
            "status itself nested": "status:\n  child: 1",
        }
        for label, frontmatter in cases.items():
            with self.subTest(label):
                parsed = handoffs.parse_handoff(f"---\n{frontmatter}\n---\n".encode("utf-8"))
                self.assertEqual(parsed.kind, "malformed")
                self.assertEqual(parsed.assertions, [])

    def test_bracketed_prefix_in_a_title_is_plain_text(self) -> None:
        parsed = handoffs.parse_handoff(b"---\nstatus: blocked\ntask: [WIP] fix the parser\n---\n")
        self.assertEqual(parsed.kind, "ok")
        self.assertEqual(parsed.fields["task"], "[WIP] fix the parser")

    def test_split_sections(self) -> None:
        sections = handoffs.split_sections("## 任務\na\n## 下一步\nb\n")
        self.assertEqual({key: value.strip() for key, value in sections.items()}, {"任務": "a", "下一步": "b"})

    def test_split_sections_ignores_text_before_first_heading_and_deeper_headings(self) -> None:
        sections = handoffs.split_sections("preamble\n## A\none\n### sub\ntwo\r\n## B\r\nthree\r\n")
        self.assertEqual(sections["A"].strip(), "one\n### sub\ntwo")
        self.assertEqual(sections["B"].strip(), "three")
        self.assertEqual(set(sections), {"A", "B"})

    def test_whitelist_matches_handoff_skill(self) -> None:
        lines = HANDOFF_SKILL.read_text(encoding="utf-8").splitlines()
        marker = next(index for index, line in enumerate(lines) if "Assertion 白名單" in line)
        kinds: set[str] = set()
        in_table = False
        for line in lines[marker + 1:]:
            if line.startswith("|"):
                in_table = True
                # Only the first cell: the parameter column also holds backticked names such as `repo`.
                match = re.match(r"\|\s*`(\w+)`\s*\|", line)
                if match:
                    kinds.add(match.group(1))
            elif in_table:
                break
        self.assertTrue(kinds)
        self.assertEqual(kinds, set(handoffs.ASSERTION_KINDS))


class CheckTests(RepoTestCase):
    def outcome(self, item: dict) -> dict:
        return handoffs.run_assertion(item)

    def test_fixture_isolated_from_global_git_config(self) -> None:
        result = run_git(self.repo, "config", "--get", "core.excludesFile", check=False)
        self.assertNotEqual(result.returncode, 0)

    def test_expect_head_pass_and_fail(self) -> None:
        head = self.head()
        for value in (head[:7], head):
            with self.subTest(value=value):
                self.assertEqual(self.outcome({"kind": "expect_head", "repo": str(self.repo), "value": value})["result"], "pass")
        failed = self.outcome({"kind": "expect_head", "repo": str(self.repo), "value": "0000000"})
        self.assertEqual(failed["result"], "fail")
        self.assertEqual(failed["kind"], "expect_head")
        self.assertIn("0000000", failed["detail"])

    def test_empty_or_missing_parameter_is_unverified(self) -> None:
        # str.startswith("") is True, so an empty value must never reach the comparison.
        for item in (
            {"kind": "expect_head", "repo": str(self.repo), "value": ""},
            {"kind": "expect_head", "repo": str(self.repo)},
            {"kind": "branch_is", "repo": str(self.repo), "value": ""},
            {"kind": "branch_is", "repo": str(self.repo)},
            {"kind": "worktree_clean"},
            {"kind": "file_exists"},
            {"kind": "file_exists", "path": ""},
            {"kind": "file_exists", "path": "/tmp/x\x00y"},
            {},
        ):
            with self.subTest(item=item):
                self.assertEqual(self.outcome(item)["result"], "unverified")

    def test_branch_is_pass_and_fail(self) -> None:
        self.assertEqual(self.outcome({"kind": "branch_is", "repo": str(self.repo), "value": "main"})["result"], "pass")
        self.assertEqual(self.outcome({"kind": "branch_is", "repo": str(self.repo), "value": "other"})["result"], "fail")
        run_git(self.repo, "checkout", "-q", "--detach")
        detached = self.outcome({"kind": "branch_is", "repo": str(self.repo), "value": "main"})
        self.assertEqual(detached["result"], "fail")
        self.assertIn("detached", detached["detail"])

    def test_file_exists_pass_and_fail(self) -> None:
        self.assertEqual(self.outcome({"kind": "file_exists", "path": str(self.repo / "README.md")})["result"], "pass")
        self.assertEqual(self.outcome({"kind": "file_exists", "path": str(self.repo / "missing.txt")})["result"], "fail")

    def test_worktree_clean_pass_and_fail(self) -> None:
        item = {"kind": "worktree_clean", "repo": str(self.repo)}
        # A handoff file sitting in the excluded directory must not count as dirt.
        write_handoff(self.handoff_dir, "a.md", frontmatter="status: in-progress")
        self.assertEqual(self.outcome(item)["result"], "pass")
        (self.repo / "untracked.txt").write_text("x\n", encoding="utf-8")
        self.assertEqual(self.outcome(item)["result"], "fail")

    def test_unknown_kind_is_unverified(self) -> None:
        marker = self.tmp / "must-not-exist"
        result = self.outcome({"kind": "run_shell", "command": f"touch {marker}"})
        self.assertEqual(result["result"], "unverified")
        self.assertFalse(marker.exists())

    def test_relative_path_resolves_against_worktree(self) -> None:
        # handoff/SKILL.md lets the writer use repo-relative paths; they are anchored at the handoff's worktree.
        (self.repo / "pkg").mkdir()
        cases = (
            ({"kind": "file_exists", "path": "README.md"}, "pass"),
            ({"kind": "file_exists", "path": "missing.txt"}, "fail"),
            ({"kind": "file_exists", "path": "./README.md"}, "pass"),
            ({"kind": "worktree_clean", "repo": "."}, "pass"),
            ({"kind": "worktree_clean", "repo": "pkg"}, "pass"),
            ({"kind": "expect_head", "repo": ".", "value": self.head()[:7]}, "pass"),
            ({"kind": "expect_head", "repo": ".", "value": "0000000"}, "fail"),
            ({"kind": "branch_is", "repo": ".", "value": "main"}, "pass"),
            ({"kind": "branch_is", "repo": ".", "value": "other"}, "fail"),
        )
        for item, expected in cases:
            with self.subTest(item=item):
                self.assertEqual(handoffs.run_assertion(item, self.repo)["result"], expected)
        # An absolute path still wins over the base.
        absolute = {"kind": "file_exists", "path": str(self.repo / "README.md")}
        self.assertEqual(handoffs.run_assertion(absolute, self.tmp)["result"], "pass")

    def test_relative_path_without_usable_base_is_unverified(self) -> None:
        for base in (None, Path("repo"), Path("")):
            for item in (
                {"kind": "file_exists", "path": "README.md"},
                {"kind": "worktree_clean", "repo": "."},
                {"kind": "expect_head", "repo": "repo", "value": self.head()[:7]},
                {"kind": "branch_is", "repo": ".", "value": "main"},
            ):
                with self.subTest(base=base, item=item):
                    self.assertEqual(handoffs.run_assertion(item, base)["result"], "unverified")

    def test_parent_segment_is_unverified(self) -> None:
        for item in (
            {"kind": "file_exists", "path": "../repo/README.md"},
            {"kind": "file_exists", "path": "pkg/../README.md"},
            {"kind": "file_exists", "path": f"{self.repo}/../repo/README.md"},
            {"kind": "worktree_clean", "repo": ".."},
            {"kind": "worktree_clean", "repo": f"{self.repo}/pkg/.."},
            {"kind": "expect_head", "repo": "../repo", "value": self.head()[:7]},
        ):
            with self.subTest(item=item):
                self.assertEqual(handoffs.run_assertion(item, self.repo)["result"], "unverified")
        # '..' inside the worktree used as the base is rejected too.
        self.assertEqual(handoffs.run_assertion({"kind": "file_exists", "path": "README.md"},
                                                self.repo / ".." / "repo")["result"], "unverified")
        # A name that merely contains dots is an ordinary segment.
        self.assertEqual(handoffs.run_assertion({"kind": "file_exists", "path": "..hidden"}, self.repo)["result"], "fail")

    def test_non_git_repo_is_unverified(self) -> None:
        plain = self.tmp / "plain"
        plain.mkdir()
        for target in (plain, self.tmp / "does-not-exist"):
            for kind in ("expect_head", "branch_is", "worktree_clean"):
                with self.subTest(target=target.name, kind=kind):
                    result = self.outcome({"kind": kind, "repo": str(target), "value": "main"})
                    self.assertEqual(result["result"], "unverified")

    def test_git_unavailable_is_unverified(self) -> None:
        with mock.patch.object(handoffs, "git", return_value=None):
            result = self.outcome({"kind": "worktree_clean", "repo": str(self.repo)})
        self.assertEqual(result["result"], "unverified")
        self.assertIn("git", result["detail"])

    def test_check_output_shape(self) -> None:
        path = write_handoff(
            self.handoff_dir,
            "feat-x--20261018-120000.md",
            frontmatter=(
                f"branch: main\nworktree: {self.repo}\ncreated: 2026-10-18T12:00:00+08:00\n"
                f"task: 接手 PR 1\nstatus: in-progress\nassertions:\n"
                f"  - kind: expect_head\n    repo: {self.repo}\n    value: {self.head()[:7]}\n"
                f"  - kind: worktree_clean\n    repo: {self.repo}\n"
            ),
            body="## 任務\n做事\n\n## 下一步\n跑測試\n",
        )
        code, out = run_cli(SCRIPT, "check", str(path), cwd=self.repo)
        self.assertEqual(code, 0)
        self.assertEqual(
            set(out),
            {"path", "kind", "status", "task", "fields", "assertions", "sections", "sha256", "already_resumed",
             "worktree_matches_cwd"},
        )
        self.assertEqual(out["path"], str(path))
        self.assertEqual(out["kind"], "ok")
        self.assertEqual(out["status"], "in-progress")
        self.assertEqual(out["task"], "接手 PR 1")
        self.assertEqual(out["fields"]["branch"], "main")
        self.assertEqual([a["kind"] for a in out["assertions"]], ["expect_head", "worktree_clean"])
        self.assertEqual([a["result"] for a in out["assertions"]], ["pass", "pass"])
        self.assertEqual(out["sections"], {"任務": "做事", "下一步": "跑測試"})

    def test_check_cwd_option(self) -> None:
        path = write_handoff(self.handoff_dir, "a.md", frontmatter=f"status: in-progress\nworktree: {self.repo}")
        code, out = run_cli(SCRIPT, "check", str(path), "--cwd", str(self.repo), cwd=self.tmp)
        self.assertEqual(code, 0)
        self.assertIs(out["worktree_matches_cwd"], True)

    def test_check_malformed_runs_no_assertions(self) -> None:
        path = write_handoff(
            self.handoff_dir,
            "bad.md",
            frontmatter=(
                f"status: blocked\nextra:\n  child: 1\nassertions:\n  - kind: worktree_clean\n    repo: {self.repo}\n"
            ),
            body="## 任務\n壞掉的 frontmatter\n",
        )
        code, out = run_cli(SCRIPT, "check", str(path), cwd=self.repo)
        self.assertEqual(code, 0)
        self.assertEqual(out["kind"], "malformed")
        self.assertEqual(out["assertions"], [])
        self.assertIn("任務", out["sections"])
        self.assertEqual(out["status"], "blocked")

    def test_check_not_handoff_exits_2(self) -> None:
        path = self.tmp / "note.md"
        path.write_text("# not a handoff\n", encoding="utf-8")
        self.assertEqual(run_cli(SCRIPT, "check", str(path), cwd=self.repo), (2, {"error": "not_handoff"}))

    def test_check_missing_file_exits_2(self) -> None:
        self.assertEqual(run_cli(SCRIPT, "check", str(self.tmp / "nope.md"), cwd=self.repo), (2, {"error": "not_found"}))

    def test_check_unreadable_path_exits_2(self) -> None:
        code, out = run_cli(SCRIPT, "check", str(self.tmp), cwd=self.repo)
        self.assertEqual(code, 2)
        self.assertEqual(out["error"], "unreadable")

    def test_check_reports_sha256_and_resumed(self) -> None:
        pending = write_handoff(self.handoff_dir, "a.md", frontmatter="status: in-progress")
        code, out = run_cli(SCRIPT, "check", str(pending), cwd=self.repo)
        self.assertEqual(code, 0)
        self.assertEqual(out["sha256"], hashlib.sha256(pending.read_bytes()).hexdigest())
        self.assertIs(out["already_resumed"], False)
        resumed = write_handoff(self.handoff_dir, "b.md", frontmatter="status: resumed\nresumed_at: 2026-10-18T13:00:00+08:00")
        code, out = run_cli(SCRIPT, "check", str(resumed), cwd=self.repo)
        self.assertEqual(code, 0)
        self.assertIs(out["already_resumed"], True)
        self.assertEqual(out["sha256"], hashlib.sha256(resumed.read_bytes()).hexdigest())

    def test_check_worktree_mismatch(self) -> None:
        elsewhere = self.tmp / "elsewhere"
        elsewhere.mkdir()
        # A symlinked spelling of the repo path checks that both sides are compared by realpath.
        alias = self.tmp / "repo-alias"
        alias.symlink_to(self.repo, target_is_directory=True)
        cases = {"elsewhere": (elsewhere, False), "repo": (self.repo, True), "alias": (alias, True)}
        for label, (worktree, expected) in cases.items():
            with self.subTest(label):
                path = write_handoff(self.handoff_dir, f"{label}.md", frontmatter=f"status: in-progress\nworktree: {worktree}")
                _, out = run_cli(SCRIPT, "check", str(path), cwd=self.repo)
                self.assertIs(out["worktree_matches_cwd"], expected)

    def test_check_worktree_uses_git_root_of_subdirectory(self) -> None:
        sub = self.repo / "pkg" / "inner"
        sub.mkdir(parents=True)
        path = write_handoff(self.handoff_dir, "a.md", frontmatter=f"status: in-progress\nworktree: {self.repo}")
        _, out = run_cli(SCRIPT, "check", str(path), cwd=sub)
        self.assertIs(out["worktree_matches_cwd"], True)

    def test_check_worktree_without_field_is_null(self) -> None:
        path = write_handoff(self.handoff_dir, "a.md", frontmatter="status: in-progress")
        _, out = run_cli(SCRIPT, "check", str(path), cwd=self.repo)
        self.assertIsNone(out["worktree_matches_cwd"])

    def test_check_resolves_relative_paths_against_handoff_worktree(self) -> None:
        assertions = (
            "assertions:\n"
            "  - kind: file_exists\n    path: README.md\n"
            "  - kind: worktree_clean\n    repo: .\n"
            "  - kind: branch_is\n    repo: .\n    value: main\n"
            "  - kind: file_exists\n    path: ../escape.txt\n"
        )
        # cwd is outside the repo on purpose: the answer must come from the handoff's worktree, not from where it runs.
        anchored = write_handoff(self.handoff_dir, "a.md", frontmatter=f"status: in-progress\nworktree: {self.repo}\n{assertions}")
        code, out = run_cli(SCRIPT, "check", str(anchored), cwd=self.tmp)
        self.assertEqual(code, 0)
        self.assertEqual([a["result"] for a in out["assertions"]], ["pass", "pass", "pass", "unverified"])

        unanchored = write_handoff(self.handoff_dir, "b.md", frontmatter=f"status: in-progress\n{assertions}")
        _, out = run_cli(SCRIPT, "check", str(unanchored), cwd=self.repo)
        self.assertEqual([a["result"] for a in out["assertions"]], ["unverified"] * 4)

        relative_worktree = write_handoff(self.handoff_dir, "c.md", frontmatter=f"status: in-progress\nworktree: repo\n{assertions}")
        _, out = run_cli(SCRIPT, "check", str(relative_worktree), cwd=self.tmp)
        self.assertEqual([a["result"] for a in out["assertions"]], ["unverified"] * 4)

    def test_check_ignores_inherited_git_repository_variables(self) -> None:
        # Hooks and wrappers export GIT_DIR / GIT_WORK_TREE, which outrank `git -C`; answers must still describe the
        # repo named in the handoff. The other repo differs in branch, HEAD and cleanliness so any leak is visible.
        other = make_repo(self.tmp / "other")
        run_git(other, "checkout", "-q", "-b", "elsewhere")
        (other / "extra.txt").write_text("second\n", encoding="utf-8")
        run_git(other, "add", "extra.txt")
        run_git(other, "commit", "-q", "-m", "second")
        (other / "dirty.txt").write_text("untracked\n", encoding="utf-8")
        other_head = run_git(other, "rev-parse", "HEAD").stdout.strip()
        self.assertNotEqual(other_head, self.head())

        sub = self.repo / "pkg"
        sub.mkdir()
        path = write_handoff(
            self.handoff_dir,
            "a.md",
            frontmatter=(
                f"status: in-progress\nworktree: {self.repo}\nassertions:\n"
                f"  - kind: branch_is\n    repo: {self.repo}\n    value: main\n"
                f"  - kind: branch_is\n    repo: {self.repo}\n    value: elsewhere\n"
                f"  - kind: expect_head\n    repo: {self.repo}\n    value: {self.head()[:7]}\n"
                f"  - kind: expect_head\n    repo: {self.repo}\n    value: {other_head[:7]}\n"
                f"  - kind: worktree_clean\n    repo: {self.repo}\n"
            ),
        )
        leaking_envs = {
            "GIT_DIR only": {"GIT_DIR": str(other / ".git")},
            "GIT_DIR and GIT_WORK_TREE": {"GIT_DIR": str(other / ".git"), "GIT_WORK_TREE": str(other)},
            "GIT_INDEX_FILE": {"GIT_INDEX_FILE": str(other / ".git" / "index")},
        }
        for label, leaking_env in leaking_envs.items():
            with self.subTest(label):
                code, out = run_cli(SCRIPT, "check", str(path), cwd=sub, env=leaking_env)
                self.assertEqual(code, 0)
                self.assertEqual([a["result"] for a in out["assertions"]], ["pass", "fail", "pass", "fail", "pass"])
                # Run from a subdirectory: a leaked GIT_DIR makes --show-toplevel report the subdirectory itself.
                self.assertIs(out["worktree_matches_cwd"], True)

    def test_git_helper_drops_repo_selection_but_keeps_config_isolation(self) -> None:
        other = make_repo(self.tmp / "other")
        with mock.patch.dict(os.environ, {"GIT_DIR": str(other / ".git"), "GIT_INDEX_FILE": str(other / "nope")}):
            toplevel = handoffs.git(["rev-parse", "--show-toplevel"], self.repo)
            excludes = handoffs.git(["config", "--get", "core.excludesFile"], self.repo)
        self.assertEqual(Path(toplevel.stdout.strip()).resolve(), self.repo.resolve())
        # GIT_CONFIG_GLOBAL must survive, otherwise the host's global excludesFile (set on this machine) shows up.
        self.assertNotEqual(excludes.returncode, 0)

    def test_repo_selecting_env_vars(self) -> None:
        handoffs._repo_selecting_env_vars.cache_clear()
        self.addCleanup(handoffs._repo_selecting_env_vars.cache_clear)
        names = handoffs._repo_selecting_env_vars()
        for expected in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY"):
            self.assertIn(expected, names)
        self.assertFalse({"GIT_CONFIG_GLOBAL", "GIT_CONFIG_NOSYSTEM"} & names)

    def test_repo_selecting_env_vars_fall_back_when_git_cannot_be_asked(self) -> None:
        handoffs._repo_selecting_env_vars.cache_clear()
        self.addCleanup(handoffs._repo_selecting_env_vars.cache_clear)
        with mock.patch.object(handoffs.subprocess, "run", side_effect=FileNotFoundError):
            names = handoffs._repo_selecting_env_vars()
        self.assertEqual(names, frozenset(handoffs._FALLBACK_REPO_ENV_VARS))

    def test_check_outside_git_compares_against_cwd(self) -> None:
        plain = self.tmp / "plain"
        plain.mkdir()
        path = write_handoff(self.handoff_dir, "a.md", frontmatter=f"status: in-progress\nworktree: {plain}")
        _, out = run_cli(SCRIPT, "check", str(path), cwd=plain)
        self.assertIs(out["worktree_matches_cwd"], True)


# Fixed clock for every `list` run: all windows and orderings below are relative to this instant.
NOW = "2026-10-18T12:00:00+08:00"
NOW_DT = datetime.fromisoformat(NOW)


def ago(**delta: float) -> str:
    return (NOW_DT - timedelta(**delta)).isoformat()


def set_mtime(path: Path, **delta: float) -> None:
    stamp = (NOW_DT - timedelta(**delta)).timestamp()
    os.utime(path, (stamp, stamp))


@unittest.skipUnless(hasattr(time, "tzset"), "needs time.tzset")
class ParseCreatedTests(unittest.TestCase):
    def setUp(self) -> None:
        patcher = mock.patch.dict(os.environ, {"TZ": "Asia/Taipei"})
        patcher.start()
        # Cleanups run last-in first-out: restore the variable before re-reading it.
        self.addCleanup(time.tzset)
        self.addCleanup(patcher.stop)
        time.tzset()

    def test_every_format_becomes_an_aware_datetime(self) -> None:
        cases = {
            "2026-10-18T03:00:00Z": datetime(2026, 10, 18, 3, tzinfo=timezone.utc),
            "2026-10-18T11:00:00+08:00": datetime(2026, 10, 18, 3, tzinfo=timezone.utc),
            # No zone means the machine's local time, pinned to UTC+8 by TZ above.
            "2026-10-18T10:00:00": datetime(2026, 10, 18, 2, tzinfo=timezone.utc),
        }
        for value, expected in cases.items():
            with self.subTest(value):
                result = handoffs.parse_created(value, 0)
                self.assertIsNotNone(result.tzinfo)
                self.assertEqual(result, expected)

    def test_missing_or_unparseable_value_uses_mtime(self) -> None:
        for value in (None, "", "   ", "not a date", "2026-13-45T00:00:00"):
            with self.subTest(value):
                result = handoffs.parse_created(value, 1_700_000_000)
                self.assertIsNotNone(result.tzinfo)
                self.assertEqual(result.timestamp(), 1_700_000_000)


class ListTests(RepoTestCase):
    def listing(self, *args: str, cwd: Path | None = None, env: dict | None = None) -> tuple[int, dict]:
        return run_cli(SCRIPT, "list", "--now", NOW, *args, cwd=cwd or self.repo, env=env)

    def put(self, name: str, *, created: str | None = None, status: str = "in-progress", where: Path | None = None,
            mtime_ago: dict | None = None) -> Path:
        lines = [f"status: {status}", f"task: {name}"]
        if created:
            lines.append(f"created: {created}")
        path = write_handoff(where or self.handoff_dir, name, frontmatter="\n".join(lines))
        # Pin mtime so the tests never depend on the real clock.
        set_mtime(path, **(mtime_ago or {"hours": 1}))
        return path

    def put_raw(self, name: str, text: str, *, mtime_ago: dict | None = None) -> Path:
        self.handoff_dir.mkdir(parents=True, exist_ok=True)
        path = self.handoff_dir / name
        path.write_text(text, encoding="utf-8")
        set_mtime(path, **(mtime_ago or {"hours": 1}))
        return path

    def add_worktree(self, name: str, branch: str | None) -> Path:
        path = self.tmp / name
        args = ["--detach"] if branch is None else ["-b", branch]
        run_git(self.repo, "worktree", "add", "-q", *args, str(path))
        return path

    @staticmethod
    def names(out: dict) -> list[str]:
        return [Path(item["path"]).name for item in out["items"]]

    @property
    def real_handoff_dir(self) -> Path:
        # The checkout is reported by its resolved spelling (/private/var on macOS), and the CLI echoes that.
        return self.repo.resolve() / ".claude" / "handoffs"

    def test_non_git_reads_cwd_only(self) -> None:
        plain = self.tmp / "plain"
        self.put("here.md", created=ago(hours=1), where=plain / ".claude" / "handoffs")
        self.put("elsewhere.md", created=ago(hours=1))
        code, out = self.listing(cwd=plain)
        self.assertEqual(code, 0)
        self.assertEqual(set(out), {"scope", "items", "remaining", "skipped"})
        self.assertEqual(out["scope"], "cwd")
        self.assertEqual(self.names(out), ["here.md"])
        self.assertEqual((out["remaining"], out["skipped"]), (0, []))
        item = out["items"][0]
        self.assertEqual(
            set(item), {"path", "task", "status", "created", "worktree", "branch", "current", "malformed"}
        )
        self.assertIs(item["current"], True)
        self.assertIsNone(item["branch"])
        self.assertIs(item["malformed"], False)
        self.assertEqual((item["task"], item["status"]), ("here.md", "in-progress"))
        self.assertEqual(Path(item["worktree"]).resolve(), plain.resolve())

    def test_no_handoffs_directory(self) -> None:
        self.assertEqual(
            self.listing(),
            (0, {"scope": "git", "items": [], "remaining": 0, "skipped": []}),
        )

    def test_git_scans_all_worktrees_current_first(self) -> None:
        linked = self.add_worktree("linked", "feat-linked")
        self.put("main-new.md", created=ago(hours=1))
        self.put("main-old.md", created=ago(hours=9))
        self.put("linked.md", created=ago(hours=5), where=linked / ".claude" / "handoffs")

        code, out = self.listing(cwd=linked)
        self.assertEqual(code, 0)
        self.assertEqual(out["scope"], "git")
        # The current worktree comes first even though the main checkout holds a newer handoff.
        self.assertEqual(self.names(out), ["linked.md", "main-new.md", "main-old.md"])
        self.assertEqual([item["current"] for item in out["items"]], [True, False, False])
        self.assertEqual([item["branch"] for item in out["items"]], ["feat-linked", "main", "main"])
        self.assertEqual(Path(out["items"][0]["worktree"]).resolve(), linked.resolve())
        self.assertEqual(Path(out["items"][1]["worktree"]).resolve(), self.repo.resolve())

        _, out = self.listing(cwd=self.repo)
        self.assertEqual(self.names(out), ["main-new.md", "main-old.md", "linked.md"])
        self.assertEqual([item["current"] for item in out["items"]], [True, True, False])

    def test_detached_worktree_has_no_branch(self) -> None:
        detached = self.add_worktree("detached", None)
        self.put("d.md", created=ago(hours=1), where=detached / ".claude" / "handoffs")
        _, out = self.listing(cwd=detached)
        self.assertEqual(self.names(out), ["d.md"])
        self.assertIsNone(out["items"][0]["branch"])

    def test_subdirectory_cwd_uses_repo_root(self) -> None:
        self.put("a.md", created=ago(hours=1))
        sub = self.repo / "sub" / "inner"
        sub.mkdir(parents=True)
        # A handoff directory below the cwd is not the repo's and must not be read.
        self.put("decoy.md", created=ago(hours=1), where=sub / ".claude" / "handoffs")
        from_root = self.listing(cwd=self.repo)
        self.assertEqual(self.listing(cwd=sub), from_root)
        self.assertEqual(self.names(from_root[1]), ["a.md"])

    def test_ignores_inherited_git_repository_variables(self) -> None:
        # A pre-commit hook exports GIT_DIR; it must not turn the scan into one of another repository.
        other = make_repo(self.tmp / "other")
        self.put("mine.md", created=ago(hours=1))
        self.put("theirs.md", created=ago(hours=1), where=other / ".claude" / "handoffs")
        code, out = self.listing(env={"GIT_DIR": str(other / ".git"), "GIT_WORK_TREE": str(other)})
        self.assertEqual((code, out["scope"], self.names(out)), (0, "git", ["mine.md"]))

    def test_cwd_option_selects_the_directory(self) -> None:
        self.put("a.md", created=ago(hours=1))
        outside = self.tmp / "outside"
        outside.mkdir()
        code, out = self.listing("--cwd", str(self.repo), cwd=outside)
        self.assertEqual((code, self.names(out)), (0, ["a.md"]))

    def test_unusable_worktree_list_still_lists_the_current_checkout(self) -> None:
        self.put("a.md", created=ago(hours=1))
        real_git = handoffs.git

        def without_worktree_list(args: list[str], cwd: Path):
            if args[:1] == ["worktree"]:
                return None
            return real_git(args, cwd)

        sub = self.repo / "pkg"
        sub.mkdir()
        with mock.patch.object(handoffs, "git", side_effect=without_worktree_list):
            scope, locations = handoffs.discover_locations(sub)
        self.assertEqual(scope, "git")
        self.assertEqual(len(locations), 1)
        self.assertEqual(locations[0].handoffs_dir, self.real_handoff_dir)
        self.assertEqual(locations[0].worktree, self.repo.resolve())
        self.assertTrue(locations[0].current)

    def test_excludes_resumed(self) -> None:
        self.put("done.md", created=ago(hours=1), status="resumed")
        for status in ("in-progress", "blocked", "ready-for-review"):
            self.put(f"{status}.md", created=ago(hours=2), status=status)
        _, out = self.listing()
        self.assertEqual(sorted(self.names(out)), ["blocked.md", "in-progress.md", "ready-for-review.md"])
        self.assertEqual(out["remaining"], 0)

    def test_window_and_cap_with_remaining(self) -> None:
        for index in range(7):
            self.put(f"recent-{index}.md", created=ago(hours=index + 1))
        self.put("old.md", created=ago(days=8))
        code, out = self.listing()
        self.assertEqual(code, 0)
        self.assertEqual(len(out["items"]), 5)
        # What --all would add: two recent files past the cap plus the stale one.
        self.assertEqual(out["remaining"], 3)
        self.assertEqual(self.names(out), [f"recent-{index}.md" for index in range(5)])

    def test_all_lifts_window_and_cap(self) -> None:
        for index in range(7):
            self.put(f"recent-{index}.md", created=ago(hours=index + 1))
        self.put("old.md", created=ago(days=8))
        code, out = self.listing("--all")
        self.assertEqual(code, 0)
        self.assertEqual(len(out["items"]), 8)
        self.assertEqual(out["remaining"], 0)
        self.assertEqual(self.names(out)[-1], "old.md")

    def test_window_edge_is_inclusive(self) -> None:
        self.put("edge.md", created=ago(days=7))
        self.put("just-outside.md", created=ago(days=7, seconds=1))
        _, out = self.listing()
        self.assertEqual(self.names(out), ["edge.md"])
        self.assertEqual(out["remaining"], 1)

    def test_malformed_and_not_handoff_listed_with_flag(self) -> None:
        self.put("fine.md", created=ago(hours=1))
        self.put_raw("nested.md", "---\nstatus: blocked\nextra:\n  child: 1\n---\n\nbody\n")
        self.put_raw("note.md", "# just a note, no frontmatter\n")
        # `status:` with no value cannot say whether the work is finished, so it is flagged, not trusted.
        self.put_raw("blank-status.md", "---\nstatus:\ntask: blank\n---\n")
        code, out = self.listing()
        self.assertEqual(code, 0)
        by_name = {Path(item["path"]).name: item for item in out["items"]}
        self.assertEqual(set(by_name), {"fine.md", "nested.md", "note.md", "blank-status.md"})
        self.assertIs(by_name["fine.md"]["malformed"], False)
        self.assertIs(by_name["nested.md"]["malformed"], True)
        self.assertEqual(by_name["nested.md"]["status"], "blocked")
        self.assertIs(by_name["note.md"]["malformed"], True)
        self.assertIsNone(by_name["note.md"]["status"])
        self.assertIs(by_name["blank-status.md"]["malformed"], True)
        self.assertEqual(by_name["blank-status.md"]["status"], "")
        self.assertEqual(by_name["blank-status.md"]["task"], "blank")

    def test_symlink_handoff_skipped(self) -> None:
        self.put("ok.md", created=ago(hours=1))
        outside = self.tmp / "outside.md"
        outside.write_text("---\nstatus: in-progress\ntask: secret\n---\n", encoding="utf-8")
        os.symlink(outside, self.handoff_dir / "link.md")
        os.symlink(self.tmp / "nowhere.md", self.handoff_dir / "dangling.md")
        code, out = self.listing()
        self.assertEqual(code, 0)
        self.assertEqual(self.names(out), ["ok.md"])
        self.assertEqual(
            out["skipped"],
            [
                {"path": str(self.real_handoff_dir / "dangling.md"), "reason": "symlink"},
                {"path": str(self.real_handoff_dir / "link.md"), "reason": "symlink"},
            ],
        )

    def test_missing_worktree_skipped(self) -> None:
        gone = self.add_worktree("gone", "feat-gone")
        self.put("kept.md", created=ago(hours=1))
        # Deleted behind git's back and never pruned: the worktree listing still names it.
        shutil.rmtree(gone)
        code, out = self.listing()
        self.assertEqual(code, 0)
        self.assertEqual(self.names(out), ["kept.md"])
        self.assertEqual(out["skipped"], [{"path": str(self.tmp.resolve() / "gone"), "reason": "missing_worktree"}])

    @unittest.skipIf(hasattr(os, "geteuid") and os.geteuid() == 0, "root ignores file permissions")
    def test_unreadable_handoff_skipped(self) -> None:
        self.put("ok.md", created=ago(hours=1))
        locked = self.put("locked.md", created=ago(hours=1))
        locked.chmod(0)
        self.addCleanup(locked.chmod, 0o644)
        code, out = self.listing()
        self.assertEqual(code, 0)
        self.assertEqual(self.names(out), ["ok.md"])
        self.assertEqual(out["skipped"], [{"path": str(self.real_handoff_dir / "locked.md"), "reason": "unreadable"}])

    def test_only_top_level_markdown_files_are_read(self) -> None:
        self.put("top.md", created=ago(hours=1))
        self.put("nested.md", created=ago(hours=1), where=self.handoff_dir / "archive")
        self.put_raw("notes.txt", "---\nstatus: in-progress\n---\n")
        # A FIFO named like a handoff would hang a naive read.
        (self.handoff_dir / "dir.md").mkdir()
        os.mkfifo(self.handoff_dir / "pipe.md")
        code, out = self.listing()
        self.assertEqual(code, 0)
        self.assertEqual(self.names(out), ["top.md"])
        self.assertEqual(out["skipped"], [])

    def test_created_missing_falls_back_to_mtime(self) -> None:
        self.put_raw("stale.md", "---\nstatus: in-progress\ntask: stale\n---\n", mtime_ago={"days": 10})
        self.put_raw("fresh.md", "---\nstatus: in-progress\ntask: fresh\n---\n", mtime_ago={"days": 1})
        code, out = self.listing()
        self.assertEqual(code, 0)
        self.assertEqual(self.names(out), ["fresh.md"])
        self.assertEqual(datetime.fromisoformat(out["items"][0]["created"]), NOW_DT - timedelta(days=1))
        # Hidden by the window but announced, because --all would list it.
        self.assertEqual(out["remaining"], 1)
        _, everything = self.listing("--all")
        self.assertEqual(self.names(everything), ["fresh.md", "stale.md"])
        self.assertEqual(everything["remaining"], 0)

    def test_unparseable_created_falls_back_to_mtime(self) -> None:
        self.put("garbled.md", created="last tuesday", mtime_ago={"days": 10})
        self.put("sane.md", created="yesterday-ish", mtime_ago={"days": 2})
        _, out = self.listing()
        self.assertEqual(self.names(out), ["sane.md"])

    def test_created_formats_compare(self) -> None:
        self.put("naive.md", created="2026-10-18T10:00:00")
        self.put("zulu.md", created="2026-10-18T03:30:00Z")
        self.put("offset.md", created="2026-10-18T11:00:00+08:00")
        # Newest first. The zone-less value is local time, so its place depends on the TZ the CLI runs under.
        expected = {
            "Asia/Taipei": ["zulu.md", "offset.md", "naive.md"],  # 03:30Z, 03:00Z, 02:00Z
            "America/Los_Angeles": ["naive.md", "zulu.md", "offset.md"],  # 17:00Z, 03:30Z, 03:00Z
        }
        for zone, names in expected.items():
            with self.subTest(zone):
                code, out = self.listing(env={"TZ": zone})
                self.assertEqual(code, 0)
                self.assertEqual(self.names(out), names)

    def test_unicode_and_space_filenames(self) -> None:
        name = "feat-中文 x--20261018-100000.md"
        self.put(name, created=ago(hours=1))
        code, out = self.listing()
        self.assertEqual(code, 0)
        self.assertEqual(self.names(out), [name])
        self.assertEqual(out["items"][0]["task"], name)

    def test_git_unavailable_falls_back_to_cwd(self) -> None:
        self.put("a.md", created=ago(hours=1))
        empty_bin = self.tmp / "empty-bin"
        empty_bin.mkdir()
        self.assertIsNone(shutil.which("git", path=str(empty_bin)))
        self.assertEqual(self.listing()[1]["scope"], "git")
        # run_cli launches the absolute sys.executable, so an empty PATH removes git and nothing else.
        code, out = self.listing(env={"PATH": str(empty_bin)})
        self.assertEqual(code, 0)
        self.assertEqual(out["scope"], "cwd")
        self.assertEqual(self.names(out), ["a.md"])
        self.assertIs(out["items"][0]["current"], True)
        self.assertIsNone(out["items"][0]["branch"])

    def test_invalid_now_exits_2(self) -> None:
        code, out = run_cli(SCRIPT, "list", "--now", "tomorrow", cwd=self.repo)
        self.assertEqual((code, out), (2, {"error": "invalid_now"}))


if __name__ == "__main__":
    unittest.main()
