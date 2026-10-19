"""Tests for session-start/scripts/handoffs.py: frontmatter parsing, assertions, and the check, list, mark-resumed
and delegate subcommands."""

from __future__ import annotations

import contextlib
import errno
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import stat
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

    def test_comment_that_cuts_a_bracket_in_half_is_malformed(self) -> None:
        # "[Image #2]" is what Claude Code pastes for an image; stripping "#2]" as a comment must not leave "[Image".
        for value in ("[Image #2]", "[Image #2] extra words", "{Image #2}"):
            with self.subTest(value=value):
                parsed = handoffs.parse_handoff(f"---\nstatus: blocked\ntask: {value}\n---\n".encode("utf-8"))
                self.assertEqual(parsed.kind, "malformed")

    def test_hash_comment_after_plain_text_is_still_a_comment(self) -> None:
        # YAML-correct: " #123" starts a comment, so the title is "fix". Titles that open with a closed bracket
        # pair keep the lenient plain-text reading.
        cases = {"fix #123 x": "fix", "[WIP] fix #123": "[WIP] fix", "{WIP} fix #1": "{WIP} fix"}
        for value, expected in cases.items():
            with self.subTest(value=value):
                parsed = handoffs.parse_handoff(f"---\nstatus: blocked\ntask: {value}\n---\n".encode("utf-8"))
                self.assertEqual((parsed.kind, parsed.fields["task"]), ("ok", expected))

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

    def test_check_directory_is_not_a_handoff(self) -> None:
        self.assertEqual(run_cli(SCRIPT, "check", str(self.tmp), cwd=self.repo), (2, {"error": "not_handoff"}))

    @unittest.skipIf(hasattr(os, "geteuid") and os.geteuid() == 0, "root ignores file permissions")
    def test_check_unreadable_file_exits_2(self) -> None:
        path = write_handoff(self.handoff_dir, "locked.md", frontmatter="status: in-progress")
        path.chmod(0)
        self.addCleanup(path.chmod, 0o644)
        code, out = run_cli(SCRIPT, "check", str(path), cwd=self.repo)
        self.assertEqual((code, out["error"]), (2, "unreadable"))

    @unittest.skipUnless(hasattr(os, "mkfifo"), "needs POSIX FIFOs")
    def test_check_fifo_is_refused_without_blocking(self) -> None:
        # Opening a FIFO for reading blocks until a writer shows up, so check must stat the path before it reads.
        fifo = self.tmp / "pipe.md"
        os.mkfifo(fifo)
        started = time.monotonic()
        try:
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "check", str(fifo)],
                cwd=str(self.repo),
                env=isolated_env(),
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=10,
            )
        except subprocess.TimeoutExpired:
            self.fail("check blocked on a FIFO")
        self.assertEqual((result.returncode, json.loads(result.stdout)), (2, {"error": "not_handoff"}))
        self.assertLess(time.monotonic() - started, 10)

    def test_check_accepts_a_dash_led_path_after_double_dash(self) -> None:
        # The skill puts "--" before the path so a file named "-x.md" is not mistaken for an option.
        path = write_handoff(self.tmp, "-x.md", frontmatter="status: in-progress\ntask: dash")
        code, out = run_cli(SCRIPT, "check", "--cwd", str(self.repo), "--", "-x.md", cwd=self.tmp)
        self.assertEqual((code, out["task"], out["path"]), (0, "dash", "-x.md"))
        self.assertEqual(out["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())

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
        # The main checkout is not the one we stand in, so it contributes only its newest handoff.
        self.assertEqual(self.names(out), ["linked.md", "main-new.md"])
        self.assertEqual([item["current"] for item in out["items"]], [True, False])
        self.assertEqual([item["branch"] for item in out["items"]], ["feat-linked", "main"])
        self.assertEqual(out["remaining"], 1)
        _, everything = self.listing("--all", cwd=linked)
        self.assertEqual(self.names(everything), ["linked.md", "main-new.md", "main-old.md"])
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

    def test_current_worktree_is_capped_with_remaining(self) -> None:
        for index in range(7):
            self.put(f"recent-{index}.md", created=ago(hours=index + 1))
        self.put("old.md", created=ago(days=15))
        code, out = self.listing()
        self.assertEqual(code, 0)
        self.assertEqual(len(out["items"]), 5)
        # What --all would add: two recent files past the cap plus the one older than 14 days.
        self.assertEqual(out["remaining"], 3)
        self.assertEqual(self.names(out), [f"recent-{index}.md" for index in range(5)])

    def test_all_lifts_window_and_cap(self) -> None:
        for index in range(7):
            self.put(f"recent-{index}.md", created=ago(hours=index + 1))
        self.put("old.md", created=ago(days=15))
        code, out = self.listing("--all")
        self.assertEqual(code, 0)
        self.assertEqual(len(out["items"]), 8)
        self.assertEqual(out["remaining"], 0)
        self.assertEqual(self.names(out)[-1], "old.md")

    def test_window_edge_is_inclusive(self) -> None:
        self.put("edge.md", created=ago(days=14))
        self.put("just-outside.md", created=ago(days=14, seconds=1))
        _, out = self.listing()
        self.assertEqual(self.names(out), ["edge.md"])
        self.assertEqual(out["remaining"], 1)

    def test_seven_to_fourteen_days_old_is_still_listed(self) -> None:
        # The old 7-day window hid a worktree's own unfinished handoff a few hours after its first week.
        self.put("week-and-a-bit.md", created=ago(days=7, hours=5))
        _, out = self.listing()
        self.assertEqual(self.names(out), ["week-and-a-bit.md"])
        self.assertEqual(out["remaining"], 0)

    def test_other_worktrees_contribute_only_their_newest_recent_one(self) -> None:
        linked = self.add_worktree("linked", "feat-linked")
        other = self.add_worktree("other", "feat-other")
        self.put("mine.md", created=ago(hours=1))
        for name, hours in (("linked-new.md", 2), ("linked-mid.md", 30), ("linked-old.md", 50)):
            self.put(name, created=ago(hours=hours), where=linked / ".claude" / "handoffs")
        self.put("other-new.md", created=ago(days=3), where=other / ".claude" / "handoffs")
        self.put("other-old.md", created=ago(days=5), where=other / ".claude" / "handoffs")
        _, out = self.listing()
        self.assertEqual(self.names(out), ["mine.md", "linked-new.md", "other-new.md"])
        self.assertEqual([item["current"] for item in out["items"]], [True, False, False])
        self.assertEqual(out["remaining"], 3)

    def test_other_worktree_older_than_window_is_not_listed(self) -> None:
        linked = self.add_worktree("linked", "feat-linked")
        self.put("mine.md", created=ago(hours=1))
        self.put("stale.md", created=ago(days=14, seconds=1), where=linked / ".claude" / "handoffs")
        _, out = self.listing()
        self.assertEqual(self.names(out), ["mine.md"])
        self.assertEqual(out["remaining"], 1)

    def test_other_worktree_newest_is_chosen_after_window_not_before(self) -> None:
        # The newest handoff of a worktree is stale, so nothing older may stand in for it.
        linked = self.add_worktree("linked", "feat-linked")
        self.put("stale-newest.md", created=ago(days=20), where=linked / ".claude" / "handoffs")
        self.put("staler.md", created=ago(days=30), where=linked / ".claude" / "handoffs")
        _, out = self.listing()
        self.assertEqual(out["items"], [])
        self.assertEqual(out["remaining"], 2)

    def test_many_other_worktrees_are_not_capped(self) -> None:
        for index in range(7):
            where = self.add_worktree(f"wt-{index}", f"feat-{index}")
            self.put(f"wt-{index}.md", created=ago(hours=index + 1), where=where / ".claude" / "handoffs")
        _, out = self.listing()
        self.assertEqual(len(out["items"]), 7)
        self.assertEqual(out["remaining"], 0)

    def test_standing_in_a_linked_worktree_makes_it_the_capped_one(self) -> None:
        linked = self.add_worktree("linked", "feat-linked")
        for index in range(6):
            self.put(f"linked-{index}.md", created=ago(hours=index + 1), where=linked / ".claude" / "handoffs")
        for index in range(4):
            self.put(f"main-{index}.md", created=ago(hours=index + 10))
        _, out = self.listing(cwd=linked)
        self.assertEqual(self.names(out), [f"linked-{index}.md" for index in range(5)] + ["main-0.md"])
        self.assertEqual(out["remaining"], 4)

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
        self.put_raw("stale.md", "---\nstatus: in-progress\ntask: stale\n---\n", mtime_ago={"days": 15})
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
        self.put("garbled.md", created="last tuesday", mtime_ago={"days": 15})
        self.put("sane.md", created="yesterday-ish", mtime_ago={"days": 2})
        _, out = self.listing()
        self.assertEqual(self.names(out), ["sane.md"])

    def test_created_formats_compare(self) -> None:
        self.put("naive.md", created="2026-10-18T10:00:00")
        self.put("zulu.md", created="2026-10-18T03:00:00Z")
        self.put("offset.md", created="2026-10-18T11:00:00+08:00")
        # Newest first. zulu and offset are the same instant, so the path breaks that tie. The zone-less value is
        # local time, so its place depends on the TZ the CLI runs under.
        expected = {
            "Asia/Taipei": ["offset.md", "zulu.md", "naive.md"],  # 03:00Z, 03:00Z, 02:00Z
            "America/Los_Angeles": ["naive.md", "offset.md", "zulu.md"],  # 17:00Z, 03:00Z, 03:00Z
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


class MarkResumedTests(RepoTestCase):
    NOW = "2026-10-18T12:00:00+08:00"

    def sha(self, path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def mark(self, path: Path, sha: str | None = None, now: str | None = NOW) -> tuple[int, dict]:
        args = ["mark-resumed", str(path), "--expect-sha256", self.sha(path) if sha is None else sha]
        if now is not None:
            args += ["--now", now]
        return run_cli(SCRIPT, *args, cwd=self.repo)

    def mark_in_process(self, path: Path) -> tuple[int, dict]:
        """For tests that patch the module; a CLI subprocess would not see the patch."""
        buffer = io.StringIO()
        argv = ["mark-resumed", str(path), "--expect-sha256", self.sha(path), "--now", self.NOW]
        with contextlib.redirect_stdout(buffer):
            code = handoffs.main(argv)
        return code, json.loads(buffer.getvalue())

    def snapshot(self, path: Path) -> tuple:
        """Everything a refused run must leave alone: bytes, mode, mtime and the directory listing (no temp file)."""
        info = path.stat()
        return path.read_bytes(), stat.S_IMODE(info.st_mode), info.st_mtime_ns, sorted(os.listdir(path.parent))

    def assert_refused(self, path: Path, error: str, *, sha: str | None = None) -> None:
        before = self.snapshot(path)
        self.assertEqual(self.mark(path, sha=sha), (3, {"error": error}))
        self.assertEqual(self.snapshot(path), before)

    def test_marks_status_and_adds_resumed_at(self) -> None:
        path = write_handoff(self.handoff_dir, "a.md", frontmatter="status: in-progress\ntask: keep me")
        _, checked = run_cli(SCRIPT, "check", str(path), cwd=self.repo)
        # The hash comes from `check`, not from this test, so both commands are shown to hash the same bytes.
        code, out = run_cli(
            SCRIPT, "mark-resumed", str(path), "--expect-sha256", checked["sha256"], "--now", self.NOW, cwd=self.repo
        )
        self.assertEqual((code, out), (0, {"path": str(path), "status": "resumed", "resumed_at": self.NOW}))
        _, after = run_cli(SCRIPT, "check", str(path), cwd=self.repo)
        self.assertEqual(after["fields"], {"status": "resumed", "task": "keep me", "resumed_at": self.NOW})
        self.assertIs(after["already_resumed"], True)

    def test_whole_file_rewrite_keeps_everything_else(self) -> None:
        # The template's status line carries a trailing comment and its assertions follow it.
        old_line = "status: in-progress   # a | b\n"
        new_lines = f"status: resumed\nresumed_at: {self.NOW}\n"
        for crlf, bom in ((False, False), (True, True), (True, False)):
            with self.subTest(crlf=crlf, bom=bom):
                path = self.tmp / f"template-{int(crlf)}{int(bom)}.md"
                path.write_bytes(template_bytes(crlf=crlf, bom=bom))
                expected = f"---\n{TEMPLATE_FRONTMATTER}---\n\n{TEMPLATE_BODY}"
                self.assertIn(old_line, expected)
                expected = expected.replace(old_line, new_lines)
                if crlf:
                    expected = expected.replace("\n", "\r\n")
                expected_bytes = (handoffs.BOM if bom else b"") + expected.encode("utf-8")
                self.assertEqual(self.mark(path)[0], 0)
                self.assertEqual(path.read_bytes(), expected_bytes)

    def test_body_bytes_unchanged(self) -> None:
        body = "## 任務\r\n中文  \n\n---\nstatus: nope\r\n最後沒換行".encode("utf-8")
        raw = b"---\nstatus: blocked\ntask: t\n---\n" + body
        path = self.tmp / "body.md"
        path.write_bytes(raw)
        before = handoffs.parse_handoff(raw)
        self.assertEqual(self.mark(path)[0], 0)
        updated = path.read_bytes()
        after = handoffs.parse_handoff(updated)
        self.assertEqual(updated[after.body_offset:], raw[before.body_offset:])
        self.assertTrue(updated.endswith(body))

    def test_hash_mismatch_refuses_and_leaves_file(self) -> None:
        path = write_handoff(self.handoff_dir, "a.md", frontmatter="status: in-progress")
        stale = self.sha(path)
        self.assert_refused(path, "hash_mismatch", sha="0" * 64)
        # The realistic case: another session edits the file between `check` and `mark-resumed`.
        path.write_text(path.read_text(encoding="utf-8") + "late edit\n", encoding="utf-8")
        self.assert_refused(path, "hash_mismatch", sha=stale)

    def test_already_resumed_refuses(self) -> None:
        for number, line in enumerate(("status: resumed", "status: 'resumed'   # done")):
            with self.subTest(line=line):
                path = write_handoff(self.handoff_dir, f"r{number}.md", frontmatter=line)
                self.assert_refused(path, "already_resumed")

    def test_malformed_refuses(self) -> None:
        shapes = {"nested": "status: in-progress\nmeta:\n  nested: 1", "duplicate": "status: a\nstatus: b"}
        for name, frontmatter in shapes.items():
            with self.subTest(shape=name):
                self.assert_refused(write_handoff(self.handoff_dir, f"{name}.md", frontmatter=frontmatter), "malformed")

    def test_not_handoff_refuses(self) -> None:
        plain = self.tmp / "note.md"
        plain.write_text("# not a handoff\n", encoding="utf-8")
        self.assert_refused(plain, "not_handoff")
        no_status = write_handoff(self.handoff_dir, "nostatus.md", frontmatter="task: x")
        self.assert_refused(no_status, "not_handoff")

    def test_directory_is_refused_without_being_read(self) -> None:
        # A FIFO named *.md would block a read, so anything that is not a regular file is refused up front.
        directory = self.handoff_dir / "dir.md"
        directory.mkdir(parents=True)
        self.assertEqual(self.mark(directory, sha="0" * 64), (3, {"error": "not_handoff"}))

    def test_dash_led_path_after_double_dash(self) -> None:
        # Options come first: everything after "--" is positional, so --expect-sha256 must precede it.
        path = write_handoff(self.tmp, "-x.md", frontmatter="status: in-progress")
        code, out = run_cli(
            SCRIPT, "mark-resumed", "--expect-sha256", self.sha(path), "--now", self.NOW, "--", "-x.md", cwd=self.tmp
        )
        self.assertEqual((code, out), (0, {"path": "-x.md", "status": "resumed", "resumed_at": self.NOW}))
        self.assertIn(b"status: resumed", path.read_bytes())

    def test_symlink_refuses(self) -> None:
        real = write_handoff(self.tmp, "real.md", frontmatter="status: in-progress")
        self.handoff_dir.mkdir(parents=True, exist_ok=True)
        link = self.handoff_dir / "link.md"
        link.symlink_to(real)
        dangling = self.handoff_dir / "dangling.md"
        dangling.symlink_to(self.tmp / "missing.md")
        before = real.read_bytes()
        for candidate in (link, dangling):
            with self.subTest(link=candidate.name):
                self.assertEqual(self.mark(candidate, sha=self.sha(real)), (3, {"error": "symlink"}))
                self.assertTrue(candidate.is_symlink())
        self.assertEqual(os.readlink(link), str(real))
        self.assertEqual(real.read_bytes(), before)

    def test_missing_file_exits_2(self) -> None:
        self.assertEqual(self.mark(self.tmp / "nope.md", sha="0" * 64), (2, {"error": "not_found"}))
        not_a_directory = self.tmp / "file.md"
        not_a_directory.write_text("x", encoding="utf-8")
        self.assertEqual(self.mark(not_a_directory / "child.md", sha="0" * 64), (2, {"error": "not_found"}))

    def test_refusal_order_is_symlink_then_hash_then_kind_then_status(self) -> None:
        wrong = "0" * 64
        real = write_handoff(self.tmp, "real.md", frontmatter="status: in-progress")
        self.handoff_dir.mkdir(parents=True, exist_ok=True)
        link = self.handoff_dir / "link.md"
        link.symlink_to(real)
        # Malformed AND already resumed: the file's shape is judged before its status.
        broken = write_handoff(self.handoff_dir, "broken.md", frontmatter="status: resumed\nmeta:\n  nested: 1")
        plain = self.tmp / "note.md"
        plain.write_text("# not a handoff\n", encoding="utf-8")
        cases = (
            (link, wrong, "symlink"),
            (broken, wrong, "hash_mismatch"),
            (broken, None, "malformed"),
            (plain, wrong, "hash_mismatch"),
            (plain, None, "not_handoff"),
        )
        for path, sha, error in cases:
            with self.subTest(path=path.name, wrong_hash=sha is not None, error=error):
                self.assertEqual(self.mark(path, sha=sha)[1], {"error": error})

    def test_permissions_preserved(self) -> None:
        # mkstemp creates 0o600 anyway, so the other modes are what prove the original mode is copied back.
        for mode in (0o600, 0o644, 0o444, 0o755):
            with self.subTest(mode=oct(mode)):
                path = write_handoff(self.handoff_dir, f"m{mode:o}.md", frontmatter="status: in-progress")
                path.chmod(mode)
                self.assertEqual(self.mark(path)[0], 0)
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), mode)
                self.assertEqual(handoffs.parse_handoff(path.read_bytes()).fields["status"], "resumed")

    def test_existing_resumed_at_replaced_in_place_not_duplicated(self) -> None:
        old = "resumed_at: 2026-01-01T00:00:00+00:00"
        new = f"resumed_at: {self.NOW}"
        layouts = {
            # name: (frontmatter before, frontmatter after)
            "after_status": (f"status: in-progress\ntask: x\n{old}", f"status: resumed\ntask: x\n{new}"),
            "before_status": (f"{old}\ntask: x\nstatus: in-progress", f"{new}\ntask: x\nstatus: resumed"),
            "next_to_status": (f"status: in-progress\n{old}\ntask: x", f"status: resumed\n{new}\ntask: x"),
        }
        for name, (before, after) in layouts.items():
            with self.subTest(layout=name):
                path = write_handoff(self.handoff_dir, f"{name}.md", frontmatter=before)
                self.assertEqual(self.mark(path)[0], 0)
                self.assertEqual(path.read_text(encoding="utf-8"), f"---\n{after}\n---\n\n## 任務\nx\n")
                self.assertEqual(path.read_text(encoding="utf-8").count("resumed_at:"), 1)

    def test_blank_or_commented_status_is_marked(self) -> None:
        for number, line in enumerate(("status:", "status:   # todo", 'status: "in-progress"')):
            with self.subTest(line=line):
                path = write_handoff(self.handoff_dir, f"s{number}.md", frontmatter=f"{line}\ntask: x")
                self.assertEqual(self.mark(path)[0], 0)
                expected = f"---\nstatus: resumed\nresumed_at: {self.NOW}\ntask: x\n---\n\n## 任務\nx\n"
                self.assertEqual(path.read_text(encoding="utf-8"), expected)

    def test_invalid_now_exits_2_and_leaves_file(self) -> None:
        path = write_handoff(self.handoff_dir, "a.md", frontmatter="status: in-progress")
        before = self.snapshot(path)
        self.assertEqual(self.mark(path, now="tomorrow"), (2, {"error": "invalid_now"}))
        self.assertEqual(self.snapshot(path), before)

    def test_now_formats(self) -> None:
        cases = {
            "2026-10-18T12:00:00Z": "2026-10-18T12:00:00+00:00",
            "2026-10-18T12:00:00.987654+08:00": "2026-10-18T12:00:00+08:00",
        }
        for number, (given, expected) in enumerate(cases.items()):
            with self.subTest(now=given):
                path = write_handoff(self.handoff_dir, f"n{number}.md", frontmatter="status: in-progress")
                self.assertEqual(self.mark(path, now=given)[1]["resumed_at"], expected)
        # A zone-less value is the caller's local time, so an offset is attached without moving the clock.
        path = write_handoff(self.handoff_dir, "naive.md", frontmatter="status: in-progress")
        stamp = self.mark(path, now="2026-10-18T12:00:00")[1]["resumed_at"]
        self.assertRegex(stamp, r"^2026-10-18T12:00:00[+-]\d\d:\d\d$")

    def test_default_now_is_local_time_with_offset(self) -> None:
        path = write_handoff(self.handoff_dir, "a.md", frontmatter="status: in-progress")
        stamp = datetime.fromisoformat(self.mark(path, now=None)[1]["resumed_at"])
        self.assertIsNotNone(stamp.tzinfo)
        self.assertLess(abs(datetime.now(timezone.utc) - stamp), timedelta(minutes=1))

    def test_second_mark_is_refused_and_list_drops_it(self) -> None:
        path = write_handoff(self.handoff_dir, "a.md", frontmatter="status: in-progress")
        self.assertEqual(self.mark(path)[0], 0)
        self.assertEqual(self.mark(path), (3, {"error": "already_resumed"}))
        code, listed = run_cli(SCRIPT, "list", "--all", cwd=self.repo)
        self.assertEqual((code, listed["items"]), (0, []))

    def test_rewrite_that_does_not_round_trip_is_refused_without_writing(self) -> None:
        path = write_handoff(self.handoff_dir, "a.md", frontmatter="status: in-progress\ntask: x")
        before = self.snapshot(path)
        real_parse = handoffs.parse_handoff
        calls: list[bytes] = []

        def drifting(raw: bytes):
            calls.append(raw)
            parsed = real_parse(raw)
            if len(calls) == 2:  # the re-parse of the rewritten bytes
                parsed.fields["task"] = "changed by the rewrite"
            return parsed

        with mock.patch.object(handoffs, "parse_handoff", side_effect=drifting):
            result = self.mark_in_process(path)
        self.assertEqual(len(calls), 2)
        self.assertEqual(result, (3, {"error": "malformed"}))
        self.assertEqual(self.snapshot(path), before)

    def test_failed_replace_cleans_up_and_leaves_file(self) -> None:
        path = write_handoff(self.handoff_dir, "a.md", frontmatter="status: in-progress")
        before = self.snapshot(path)
        with mock.patch.object(handoffs.os, "replace", side_effect=OSError(errno.EXDEV, "boom")):
            code, out = self.mark_in_process(path)
        self.assertEqual((code, out["error"]), (2, "unwritable"))
        self.assertEqual(self.snapshot(path), before)

    @unittest.skipIf(hasattr(os, "geteuid") and os.geteuid() == 0, "root ignores directory permissions")
    def test_read_only_directory_is_unwritable(self) -> None:
        path = write_handoff(self.handoff_dir, "a.md", frontmatter="status: in-progress")
        before = self.snapshot(path)
        self.handoff_dir.chmod(0o555)
        self.addCleanup(self.handoff_dir.chmod, 0o755)
        code, out = self.mark(path)
        self.assertEqual((code, out["error"]), (2, "unwritable"))
        self.assertEqual(self.snapshot(path), before)

    @unittest.skipIf(hasattr(os, "geteuid") and os.geteuid() == 0, "root ignores file permissions")
    def test_unreadable_file_exits_2(self) -> None:
        path = write_handoff(self.handoff_dir, "a.md", frontmatter="status: in-progress")
        path.chmod(0)
        self.addCleanup(path.chmod, 0o644)
        code, out = self.mark(path, sha="0" * 64)
        self.assertEqual((code, out["error"]), (2, "unreadable"))


class DelegateTests(RepoTestCase):
    """`delegate` runs a copy of the script from install/, so "self" never coincides with a candidate unless a test
    wants it to."""

    def setUp(self) -> None:
        super().setUp()
        self.home = self.tmp / "home"
        self.home.mkdir()
        self.install = self.tmp / "install" / "session-start"
        (self.install / "scripts").mkdir(parents=True)
        (self.install / "SKILL.md").write_text("generic\n", encoding="utf-8")
        self.script = self.install / "scripts" / "handoffs.py"
        shutil.copy2(SCRIPT, self.script)

    @staticmethod
    def skill(skills_dir: Path, text: str = "local\n") -> Path:
        path = skills_dir / "session-start" / "SKILL.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def delegate(self, runtime: str, *args: str, cwd: Path | None = None, script: Path | None = None,
                 env: dict | None = None) -> dict:
        code, out = run_cli(
            script or self.script, "delegate", "--runtime", runtime, *args,
            cwd=cwd or self.repo, env={"HOME": str(self.home), **(env or {})},
        )
        self.assertEqual(code, 0)
        return out

    def test_user_level_roots(self) -> None:
        home = Path("/h")
        self.assertEqual(
            handoffs.user_level_roots(home),
            [home / ".claude" / "skills", home / ".codex" / "skills", home / ".omp" / "agent" / "skills",
             home / ".claude" / "plugins", home / ".codex" / "plugins"],
        )

    def test_self_skill_sits_next_to_scripts_dir(self) -> None:
        self.assertEqual(handoffs.SELF_SKILL, SCRIPT.resolve().parent.parent / "SKILL.md")

    def test_no_candidate_returns_null(self) -> None:
        out = self.delegate("claude")
        self.assertEqual(set(out), {"root", "delegate", "candidates", "drift", "excluded"})
        self.assertIsNone(out["delegate"])
        self.assertEqual(out["candidates"], [])
        self.assertIs(out["drift"], False)
        self.assertEqual(out["excluded"], [])

    def test_claude_runtime_prefers_dot_claude_and_reports_drift(self) -> None:
        self.skill(self.repo / ".claude" / "skills", "claude copy\n")
        self.skill(self.repo / ".codex" / "skills", "codex copy\n")
        out = self.delegate("claude")
        self.assertTrue(out["delegate"].endswith("/.claude/skills/session-start/SKILL.md"), out["delegate"])
        self.assertEqual(len(out["candidates"]), 2)
        self.assertEqual(out["delegate"], out["candidates"][0])
        self.assertTrue(out["candidates"][1].endswith("/.codex/skills/session-start/SKILL.md"), out["candidates"])
        self.assertIs(out["drift"], True)
        self.assertEqual(out["excluded"], [])

    def test_codex_runtime_prefers_dot_codex(self) -> None:
        self.skill(self.repo / ".claude" / "skills", "claude copy\n")
        self.skill(self.repo / ".codex" / "skills", "codex copy\n")
        out = self.delegate("codex")
        self.assertTrue(out["delegate"].endswith("/.codex/skills/session-start/SKILL.md"), out["delegate"])
        self.assertTrue(out["candidates"][1].endswith("/.claude/skills/session-start/SKILL.md"), out["candidates"])
        self.assertIs(out["drift"], True)

    def test_only_one_runtime_dir_present(self) -> None:
        self.skill(self.repo / ".codex" / "skills")
        for runtime in ("claude", "codex"):
            with self.subTest(runtime=runtime):
                out = self.delegate(runtime)
                self.assertTrue(out["delegate"].endswith("/.codex/skills/session-start/SKILL.md"), out["delegate"])
                self.assertEqual(len(out["candidates"]), 1)
                self.assertIs(out["drift"], False)

    def test_symlinked_codex_dir_dedupes(self) -> None:
        self.skill(self.repo / ".claude" / "skills")
        (self.repo / ".codex").mkdir()
        (self.repo / ".codex" / "skills").symlink_to(Path("..") / ".claude" / "skills")
        for runtime, first in (("claude", ".claude"), ("codex", ".codex")):
            with self.subTest(runtime=runtime):
                out = self.delegate(runtime)
                self.assertEqual(len(out["candidates"]), 1)
                # The first candidate in runtime order is the one kept, under the spelling it was found by.
                self.assertTrue(out["delegate"].endswith(f"/{first}/skills/session-start/SKILL.md"), out["delegate"])
                self.assertIs(out["drift"], False)

    def test_identical_distinct_files_no_drift(self) -> None:
        self.skill(self.repo / ".claude" / "skills", "same\n")
        self.skill(self.repo / ".codex" / "skills", "same\n")
        out = self.delegate("claude")
        self.assertEqual(len(out["candidates"]), 2)
        self.assertIs(out["drift"], False)

    def test_self_is_excluded(self) -> None:
        own = self.repo / ".claude" / "skills" / "session-start"
        (own / "scripts").mkdir(parents=True)
        shutil.copy2(SCRIPT, own / "scripts" / "handoffs.py")
        self.skill(self.repo / ".claude" / "skills", "this is the running skill\n")
        out = self.delegate("claude", script=own / "scripts" / "handoffs.py")
        self.assertIsNone(out["delegate"])
        self.assertEqual(out["candidates"], [])
        self.assertEqual([entry["reason"] for entry in out["excluded"]], ["self"])
        self.assertTrue(out["excluded"][0]["path"].endswith("/.claude/skills/session-start/SKILL.md"))

    def test_self_excluded_but_the_other_copy_still_delegates(self) -> None:
        own = self.repo / ".claude" / "skills" / "session-start"
        (own / "scripts").mkdir(parents=True)
        shutil.copy2(SCRIPT, own / "scripts" / "handoffs.py")
        self.skill(self.repo / ".claude" / "skills")
        self.skill(self.repo / ".codex" / "skills")
        out = self.delegate("claude", script=own / "scripts" / "handoffs.py")
        self.assertTrue(out["delegate"].endswith("/.codex/skills/session-start/SKILL.md"), out["delegate"])
        self.assertEqual(len(out["candidates"]), 1)
        self.assertIs(out["drift"], False)
        self.assertEqual([entry["reason"] for entry in out["excluded"]], ["self"])

    def test_production_layout_is_self(self) -> None:
        # ~/.claude/skills points at a separate checkout, and the skill runs through that symlink.
        prod = self.tmp / "prod"
        self.skill(prod, "user-level\n")
        (prod / "session-start" / "scripts").mkdir()
        shutil.copy2(SCRIPT, prod / "session-start" / "scripts" / "handoffs.py")
        (self.home / ".claude").mkdir()
        (self.home / ".claude" / "skills").symlink_to(prod)
        script = self.home / ".claude" / "skills" / "session-start" / "scripts" / "handoffs.py"
        out = self.delegate("claude", cwd=self.home, script=script)
        self.assertIsNone(out["delegate"])
        self.assertEqual([entry["reason"] for entry in out["excluded"]], ["self"])

    def test_user_level_excluded_in_non_git_home(self) -> None:
        prod = self.tmp / "prod"
        self.skill(prod)
        (self.home / ".claude").mkdir()
        (self.home / ".claude" / "skills").symlink_to(prod)
        # --cwd arrives as the literal spelling, unlike a process cwd, which the OS reports already resolved.
        out = self.delegate("claude", "--cwd", str(self.home), cwd=self.tmp)
        self.assertIsNone(out["delegate"])
        self.assertEqual(out["candidates"], [])
        self.assertEqual([entry["reason"] for entry in out["excluded"]], ["user_level"])
        self.assertEqual(Path(out["root"]), self.home.resolve())

    def test_user_level_skill_that_is_a_symlink_elsewhere_is_excluded(self) -> None:
        # The target's realpath is under no user-level root, so only the candidate's own spelling can match.
        target = self.tmp / "elsewhere" / "SKILL.md"
        target.parent.mkdir()
        target.write_text("user-level\n", encoding="utf-8")
        link = self.home / ".claude" / "skills" / "session-start" / "SKILL.md"
        link.parent.mkdir(parents=True)
        link.symlink_to(target)
        out = self.delegate("claude", cwd=self.home)
        self.assertIsNone(out["delegate"])
        self.assertEqual([entry["reason"] for entry in out["excluded"]], ["user_level"])

    def test_repo_skills_dir_linked_into_user_level_is_excluded(self) -> None:
        self.skill(self.home / ".claude" / "skills", "user-level\n")
        (self.repo / ".claude").mkdir()
        (self.repo / ".claude" / "skills").symlink_to(self.home / ".claude" / "skills")
        self.skill(self.repo / ".codex" / "skills", "repo-local\n")
        out = self.delegate("claude")
        self.assertTrue(out["delegate"].endswith("/.codex/skills/session-start/SKILL.md"), out["delegate"])
        self.assertEqual(len(out["candidates"]), 1)
        self.assertIs(out["drift"], False)
        self.assertEqual([entry["reason"] for entry in out["excluded"]], ["user_level"])

    def test_plugin_roots_are_user_level(self) -> None:
        (self.repo / ".claude").mkdir()
        link = self.repo / ".claude" / "skills"
        for tool in (".claude", ".codex"):
            with self.subTest(tool=tool):
                cache = self.home / tool / "plugins" / "cache" / "x"
                self.skill(cache, "plugin copy\n")
                link.unlink(missing_ok=True)
                link.symlink_to(cache)
                out = self.delegate("claude")
                self.assertIsNone(out["delegate"])
                self.assertEqual([entry["reason"] for entry in out["excluded"]], ["user_level"])

    def test_non_git_uses_cwd_root(self) -> None:
        plain = self.tmp / "plain"
        self.skill(plain / ".claude" / "skills")
        out = self.delegate("claude", cwd=plain)
        self.assertEqual(Path(out["root"]), plain.resolve())
        self.assertEqual(Path(out["delegate"]), plain.resolve() / ".claude" / "skills" / "session-start" / "SKILL.md")

    def test_git_root_is_used_from_a_subdirectory(self) -> None:
        self.skill(self.repo / ".claude" / "skills")
        sub = self.repo / "pkg" / "deep"
        sub.mkdir(parents=True)
        out = self.delegate("claude", cwd=sub)
        self.assertEqual(Path(out["root"]), self.repo.resolve())
        self.assertIsNotNone(out["delegate"])

    def test_cwd_option_overrides_process_cwd(self) -> None:
        self.skill(self.repo / ".claude" / "skills")
        out = self.delegate("claude", "--cwd", str(self.repo), cwd=self.tmp)
        self.assertEqual(Path(out["root"]), self.repo.resolve())
        self.assertIsNotNone(out["delegate"])

    def test_git_unavailable_falls_back_to_cwd(self) -> None:
        self.skill(self.repo / ".claude" / "skills")
        sub = self.repo / "pkg"
        self.skill(sub / ".claude" / "skills", "nested\n")
        empty_bin = self.tmp / "empty-bin"
        empty_bin.mkdir()
        self.assertIsNone(shutil.which("git", path=str(empty_bin)))
        self.assertEqual(Path(self.delegate("claude", cwd=sub)["root"]), self.repo.resolve())
        # run_cli launches the absolute sys.executable, so an empty PATH removes git and nothing else.
        out = self.delegate("claude", cwd=sub, env={"PATH": str(empty_bin)})
        self.assertEqual(Path(out["root"]), sub.resolve())
        self.assertTrue(Path(out["delegate"]).is_relative_to(sub.resolve()), out["delegate"])

    def test_non_regular_or_dangling_candidates_are_ignored(self) -> None:
        (self.repo / ".claude" / "skills" / "session-start" / "SKILL.md").mkdir(parents=True)
        dangling = self.repo / ".codex" / "skills" / "session-start" / "SKILL.md"
        dangling.parent.mkdir(parents=True)
        dangling.symlink_to(self.tmp / "missing.md")
        out = self.delegate("claude")
        self.assertIsNone(out["delegate"])
        self.assertEqual((out["candidates"], out["excluded"]), ([], []))

    @unittest.skipIf(hasattr(os, "geteuid") and os.geteuid() == 0, "root ignores file permissions")
    def test_unreadable_candidate_is_reported_not_hidden(self) -> None:
        # Dropping it silently would hide the repo's own rules, so it has to show up in `excluded`.
        path = self.skill(self.repo / ".claude" / "skills")
        path.chmod(0)
        self.addCleanup(path.chmod, 0o644)
        self.skill(self.repo / ".codex" / "skills")
        out = self.delegate("claude")
        self.assertTrue(out["delegate"].endswith("/.codex/skills/session-start/SKILL.md"), out["delegate"])
        self.assertEqual([entry["reason"] for entry in out["excluded"]], ["unreadable"])
        self.assertIs(out["drift"], False)

    def test_runtime_is_required_and_validated(self) -> None:
        for args in ([], ["--runtime", "gemini"]):
            with self.subTest(args=args):
                result = subprocess.run(
                    [sys.executable, str(self.script), "delegate", *args],
                    cwd=str(self.repo), env=isolated_env({"HOME": str(self.home)}),
                    capture_output=True, text=True, timeout=30,
                )
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertIn("--runtime", result.stderr)


if __name__ == "__main__":
    unittest.main()
