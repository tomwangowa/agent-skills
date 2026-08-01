from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import find_referenced_documents as analyzer  # noqa: E402


def write_record(
    activities_dir: Path,
    filename: str,
    timestamp: str,
    activities: list[dict[str, object]],
    project_path: Path,
):
    record = {
        "session_id": filename,
        "timestamp": f"{timestamp}T12:00:00Z",
        "project_path": str(project_path),
        "project_name": "kaleida-ai-agent",
        "git_branch": "tom/docs-audit",
        "activities": activities,
        "context": "",
        "tags": [],
    }
    (activities_dir / filename).write_text(
        json.dumps(record), encoding="utf-8"
    )


@pytest.fixture
def audit_fixture(tmp_path: Path) -> dict[str, Path]:
    checkout = tmp_path / "checkout"
    project = tmp_path / "kaleida"
    rei = tmp_path / "rei"
    worktree = tmp_path / "deleted-worktree"
    activities_dir = tmp_path / "activities"
    map_path = checkout / ".claude" / "skills" / "session-start" / "repos.yaml"
    for path in (project / "docs", project / "specs", rei / "design", activities_dir):
        path.mkdir(parents=True)

    current_doc = project / "docs" / "current.md"
    legacy_doc = project / "docs" / "legacy.md"
    mapped_doc = project / "specs" / "mapped.md"
    rei_doc = rei / "design" / "rei.md"
    current_doc.write_text("current\n", encoding="utf-8")
    legacy_doc.write_text("legacy\n", encoding="utf-8")
    mapped_doc.write_text("mapped\n", encoding="utf-8")
    rei_doc.write_text("rei\n", encoding="utf-8")

    map_path.parent.mkdir(parents=True, exist_ok=True)
    map_path.write_text(
        "repos:\n"
        "  - name: Mapped\n"
        "    type: doc\n"
        f"    path: {mapped_doc}\n"
        "  - name: Existing pinned URL\n"
        "    type: url\n"
        "    path: https://github.com/acme/existing/blob/main/docs/existing.md\n",
        encoding="utf-8",
    )
    return {
        "checkout": checkout,
        "project": project,
        "rei": rei,
        "worktree": worktree,
        "activities": activities_dir,
        "map": map_path,
        "current": current_doc,
        "legacy": legacy_doc,
        "mapped": mapped_doc,
        "rei_doc": rei_doc,
    }


def test_document_filter_and_supported_remotes():
    assert analyzer.is_document_candidate("docs/design.md")
    assert analyzer.is_document_candidate("https://example.com/specs/flow.html")
    assert analyzer.is_document_candidate("design-handoff/flow")
    assert not analyzer.is_document_candidate("src/app.py")
    assert not analyzer.is_document_candidate("http://example.com/docs/flow.md")
    assert not analyzer.is_document_candidate("https://[broken/docs/flow.md")

    assert analyzer.normalize_remote("git@github.com:acme/demo.git") == (
        "github",
        "acme/demo",
    )
    assert analyzer.normalize_remote("https://gitlab.com/group/sub/demo.git") == (
        "gitlab",
        "group/sub/demo",
    )
    assert analyzer.normalize_remote("git@example.com:acme/demo.git") is None
    assert analyzer.normalize_remote("https://[broken") is None
    assert analyzer.build_pinned_url(
        "git@github.com:acme/demo.git", "abc123", "docs/a guide.md"
    ) == "https://github.com/acme/demo/blob/abc123/docs/a%20guide.md"


def test_audit_classifies_structured_legacy_deleted_and_mapped(audit_fixture):
    fixture = audit_fixture
    deleted = fixture["worktree"] / "docs" / "deleted.md"
    untracked = fixture["worktree"] / "docs" / "untracked.md"
    modified = fixture["worktree"] / "docs" / "modified.md"
    unsupported = fixture["worktree"] / "docs" / "unsupported.md"

    write_record(
        fixture["activities"],
        "recent.json",
        "2026-07-20",
        [
            {
                "type": "research",
                "description": "Read docs/legacy.md and reviewed the contract",
                "files_changed": ["docs/legacy.md", "src/ignored.py"],
                "commits": ["docs/commit-subject.md"],
                "references": [
                    {"path": str(fixture["current"])},
                    {"path": str(fixture["rei_doc"])},
                    {
                        "path": str(deleted),
                        "repo_root": str(fixture["worktree"]),
                        "relative_path": "docs/deleted.md",
                        "remote": "git@github.com:acme/demo.git",
                        "commit": "abc123",
                        "tracked_at_log_time": True,
                        "working_tree_status": "clean",
                    },
                    {
                        "path": str(untracked),
                        "repo_root": str(fixture["worktree"]),
                        "relative_path": "docs/untracked.md",
                        "remote": "git@github.com:acme/demo.git",
                        "commit": "abc123",
                        "tracked_at_log_time": False,
                        "working_tree_status": "clean",
                    },
                    {
                        "path": str(modified),
                        "repo_root": str(fixture["worktree"]),
                        "relative_path": "docs/modified.md",
                        "remote": "git@github.com:acme/demo.git",
                        "commit": "abc123",
                        "tracked_at_log_time": True,
                        "working_tree_status": "modified",
                    },
                    {
                        "path": str(unsupported),
                        "repo_root": str(fixture["worktree"]),
                        "relative_path": "docs/unsupported.md",
                        "remote": "git@example.com:acme/demo.git",
                        "commit": "abc123",
                        "tracked_at_log_time": True,
                        "working_tree_status": "clean",
                    },
                    {"path": str(fixture["mapped"])},
                ],
            }
        ],
        fixture["project"],
    )
    write_record(
        fixture["activities"],
        "old.json",
        "2026-06-30",
        [
            {
                "type": "research",
                "description": "Read docs/outside-range.md",
                "files_changed": [],
            }
        ],
        fixture["project"],
    )
    (fixture["activities"] / "malformed.json").write_text("{", encoding="utf-8")

    payload, record_count = analyzer.analyze_references(
        fixture["activities"], fixture["map"], analyzer.date(2026, 7, 1), analyzer.date(2026, 7, 31)
    )

    assert record_count == 1
    candidates = {item["path"]: item for item in payload["candidates"]}
    assert str(fixture["current"]) in candidates
    assert str(fixture["rei_doc"]) in candidates
    assert str(fixture["legacy"]) in candidates
    assert candidates["https://github.com/acme/demo/blob/abc123/docs/deleted.md"]["status"] == "stale-worktree"
    assert all("outside-range" not in path for path in candidates)

    unresolved_paths = {item["path"] for item in payload["unresolved"]}
    assert str(untracked) in unresolved_paths
    assert str(modified) in unresolved_paths
    assert str(unsupported) in unresolved_paths
    assert len(payload["already_mapped"]) == 1
    assert payload["already_mapped"][0]["path"] == str(fixture["mapped"])
    assert len(candidates[str(fixture["legacy"])] ["evidence"]) == 2


def test_legacy_parser_does_not_infer_from_project_branch_or_commits():
    record = {
        "project_name": "docs/project-name.md",
        "project_path": "/tmp/project",
        "git_branch": "docs/branch-name.md",
        "activities": [
            {
                "description": "Fixed docs/real.md",
                "files_changed": [],
                "commits": ["docs/commit-subject.md"],
            }
        ],
    }
    values = list(analyzer.iter_legacy_paths(record))
    assert [item["raw"] for item in values] == ["docs/real.md"]


def test_json_cli_and_empty_markdown(audit_fixture, capsys):
    code = analyzer.main(
        [
            "--activities-dir",
            str(audit_fixture["activities"]),
            "--map",
            str(audit_fixture["map"]),
            "--since",
            "2026-08-01",
            "--until",
            "2026-08-01",
            "--format",
            "json",
        ]
    )
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["since"] == "2026-08-01T00:00:00Z"
    assert payload["until"] == "2026-08-01T00:00:00Z"
    assert payload["candidates"] == []

    code = analyzer.main(
        [
            "--activities-dir",
            str(audit_fixture["activities"]),
            "--map",
            str(audit_fixture["map"]),
            "--since",
            "2026-08-01",
            "--until",
            "2026-08-01",
            "--format",
            "markdown",
        ]
    )
    assert code == 0
    output = capsys.readouterr().out
    assert "No activity records matched" in output
    assert "2026-08-01T00:00:00Z" in output


def test_malformed_map_fails_before_producing_output(audit_fixture, capsys):
    audit_fixture["map"].write_text("repos: [", encoding="utf-8")

    code = analyzer.main(
        [
            "--activities-dir",
            str(audit_fixture["activities"]),
            "--map",
            str(audit_fixture["map"]),
            "--format",
            "json",
        ]
    )

    captured = capsys.readouterr()
    assert code == 2
    assert captured.out == ""
    assert "repos.yaml" in captured.err


def test_explicit_map_analysis_does_not_call_subprocess(audit_fixture, monkeypatch):
    write_record(
        audit_fixture["activities"],
        "network-check.json",
        "2026-07-20",
        [
            {
                "type": "research",
                "description": "",
                "files_changed": [],
                "references": [{"path": str(audit_fixture["current"])}],
            }
        ],
        audit_fixture["project"],
    )
    monkeypatch.setattr(
        analyzer.subprocess,
        "run",
        lambda *args, **kwargs: pytest.fail("analysis unexpectedly called a subprocess"),
    )

    payload, _ = analyzer.analyze_references(
        audit_fixture["activities"],
        audit_fixture["map"],
        analyzer.date(2026, 7, 1),
        analyzer.date(2026, 7, 31),
    )

    assert payload["candidates"]
