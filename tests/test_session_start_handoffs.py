"""Tests for session-start/scripts/handoffs.py: frontmatter parsing, assertions and the check subcommand."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
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


if __name__ == "__main__":
    unittest.main()
