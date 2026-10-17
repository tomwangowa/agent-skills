#!/usr/bin/env python3
"""Find recent, explicitly referenced documents missing from repos.yaml."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator
from urllib.parse import quote, urlsplit, urlunsplit

try:
    import yaml
except ImportError as exc:  # pragma: no cover - depends on the host interpreter
    yaml = None  # type: ignore[assignment]
    YAML_IMPORT_ERROR: ImportError | None = exc
else:
    YAML_IMPORT_ERROR = None


DOC_DIRS = {"docs", "design", "design-handoff", "specs"}
DOC_SUFFIXES = {".md", ".yaml", ".yml", ".html"}
SUPPORTED_ENTRY_TYPES = {"doc", "repo", "url"}
PATH_TOKEN_RE = re.compile(
    r"https://[^\s<>\"'`]+|(?:(?:~|\.{0,2})/|[A-Za-z0-9_.-]+/)[^\s<>\"'`,;:!?]+"
)
TRAILING_TOKEN_CHARS = ".,;:!?)]}>"


class AnalyzerError(RuntimeError):
    """Raised for invalid analysis inputs or configuration."""


def _as_date(value: date | datetime) -> date:
    return value.date() if isinstance(value, datetime) else value


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def iter_activity_records(
    activities_dir: Path, start: datetime, end: datetime
) -> Iterator[tuple[Path, dict[str, Any]]]:
    """Yield valid activity records whose top-level timestamp is in range."""

    start_date = _as_date(start)
    end_date = _as_date(end)
    if not activities_dir.is_dir():
        return

    for record_path in sorted(activities_dir.glob("*.json")):
        try:
            record = json.loads(record_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        if not isinstance(record, dict):
            continue
        timestamp = _parse_timestamp(record.get("timestamp"))
        if timestamp is None:
            continue
        if start_date <= timestamp.date() <= end_date:
            yield record_path, record


def _document_value(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = value.strip().rstrip(TRAILING_TOKEN_CHARS)
    return cleaned or None


def iter_structured_references(record: dict[str, Any]) -> Iterator[dict[str, Any]]:
    """Yield only values stored in activities[*].references."""

    activities = record.get("activities")
    if not isinstance(activities, list):
        return
    for activity_index, activity in enumerate(activities):
        if not isinstance(activity, dict):
            continue
        references = activity.get("references")
        if not isinstance(references, list):
            continue
        for reference_index, reference in enumerate(references):
            metadata: dict[str, Any]
            if isinstance(reference, str):
                metadata = {}
                raw = _document_value(reference)
            elif isinstance(reference, dict):
                metadata = reference
                raw = _document_value(
                    reference.get("path")
                    or reference.get("url")
                    or reference.get("absolute_path")
                )
                if raw is None:
                    relative = _document_value(reference.get("relative_path"))
                    repo_root = _document_value(reference.get("repo_root"))
                    if relative and repo_root:
                        raw = str(Path(repo_root) / relative)
            else:
                continue
            if raw and is_document_candidate(raw):
                yield {
                    "raw": raw,
                    "metadata": metadata,
                    "source": f"activities[{activity_index}].references[{reference_index}]",
                }


def _path_tokens(text: str) -> Iterator[str]:
    for match in PATH_TOKEN_RE.finditer(text):
        value = _document_value(match.group(0))
        if value and is_document_candidate(value):
            yield value


def iter_legacy_paths(record: dict[str, Any]) -> Iterator[dict[str, Any]]:
    """Yield explicit document paths from legacy activity fields only."""

    activities = record.get("activities")
    if isinstance(activities, list):
        for activity_index, activity in enumerate(activities):
            if not isinstance(activity, dict):
                continue
            files_changed = activity.get("files_changed")
            if isinstance(files_changed, list):
                for file_index, value in enumerate(files_changed):
                    raw = _document_value(value)
                    if raw and is_document_candidate(raw):
                        yield {
                            "raw": raw,
                            "metadata": {},
                            "source": f"activities[{activity_index}].files_changed[{file_index}]",
                        }
            for field in ("description", "context"):
                value = activity.get(field)
                if not isinstance(value, str):
                    continue
                for raw in _path_tokens(value):
                    yield {
                        "raw": raw,
                        "metadata": {},
                        "source": f"activities[{activity_index}].{field}",
                    }

    context = record.get("context")
    if isinstance(context, str):
        for raw in _path_tokens(context):
            yield {
                "raw": raw,
                "metadata": {},
                "source": "context",
            }


def is_document_candidate(path_or_url: str) -> bool:
    """Return whether a path or HTTPS URL looks like a documentation file."""

    if not isinstance(path_or_url, str) or not path_or_url.strip():
        return False
    value = path_or_url.strip()
    try:
        parsed = urlsplit(value)
    except ValueError:
        return False
    if parsed.scheme:
        if parsed.scheme.lower() != "https" or not parsed.netloc:
            return False
        candidate_path = parsed.path
    else:
        candidate_path = value
    path = Path(candidate_path)
    normalized_parts = {part.lower() for part in path.parts}
    return bool(normalized_parts & DOC_DIRS) or path.suffix.lower() in DOC_SUFFIXES


def _base_path(record: dict[str, Any]) -> Path | None:
    for key in ("project_path", "repo_root"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return Path(value).expanduser()
    return None


def resolve_legacy_path(raw: str, record: dict[str, Any]) -> Path | None:
    """Resolve an explicit legacy path using the recorded project root."""

    try:
        parsed = urlsplit(raw)
    except ValueError:
        return None
    if parsed.scheme:
        return None
    path = Path(raw).expanduser()
    if not path.is_absolute():
        base = _base_path(record)
        if base is None:
            return None
        path = base / path
    try:
        return path.resolve(strict=False)
    except (OSError, RuntimeError, ValueError):
        return None


def _resolve_structured_path(reference: dict[str, Any], record: dict[str, Any]) -> Path | None:
    raw = reference.get("raw")
    if not isinstance(raw, str):
        return None
    try:
        parsed = urlsplit(raw)
    except ValueError:
        return None
    if parsed.scheme:
        return None
    metadata = reference.get("metadata")
    metadata = metadata if isinstance(metadata, dict) else {}
    base_value = metadata.get("repo_root") or record.get("project_path")
    path = Path(raw).expanduser()
    if not path.is_absolute():
        if not isinstance(base_value, str) or not base_value.strip():
            return None
        path = Path(base_value).expanduser() / path
    try:
        return path.resolve(strict=False)
    except (OSError, RuntimeError, ValueError):
        return None


def _normalize_url(value: str) -> str | None:
    try:
        parsed = urlsplit(value.strip())
    except ValueError:
        return None
    if parsed.scheme.lower() != "https" or not parsed.netloc:
        return None
    return urlunsplit(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path,
            parsed.query,
            parsed.fragment,
        )
    )


def normalize_remote(remote: str) -> tuple[str, str] | None:
    """Normalize supported GitHub/GitLab HTTPS and SSH remotes."""

    if not isinstance(remote, str) or not remote.strip():
        return None
    value = remote.strip()
    host = ""
    repository = ""
    ssh_match = re.fullmatch(r"git@(github\.com|gitlab\.com):(.+)", value, re.I)
    if ssh_match:
        host = ssh_match.group(1).lower()
        repository = ssh_match.group(2)
    else:
        try:
            parsed = urlsplit(value)
            host = parsed.hostname
        except ValueError:
            return None
        if parsed.scheme.lower() != "https" or not host:
            return None
        host = host.lower()
        repository = parsed.path.strip("/")
    if repository.endswith(".git"):
        repository = repository[:-4]
    repository = repository.strip("/")
    if host == "github.com" and len(repository.split("/")) == 2:
        return "github", repository
    if host == "gitlab.com" and len(repository.split("/")) >= 2:
        return "gitlab", repository
    return None


def build_pinned_url(remote: str, commit: str, relative_path: str) -> str | None:
    normalized_remote = normalize_remote(remote)
    if not normalized_remote or not commit or not relative_path:
        return None
    provider, repository = normalized_remote
    clean_path = relative_path.strip().lstrip("/")
    if not clean_path or clean_path == ".":
        return None
    encoded_path = quote(clean_path, safe="/-._~:@")
    encoded_commit = quote(commit.strip(), safe="")
    if not encoded_commit:
        return None
    if provider == "github":
        return f"https://github.com/{repository}/blob/{encoded_commit}/{encoded_path}"
    return f"https://gitlab.com/{repository}/-/blob/{encoded_commit}/{encoded_path}"


def _metadata_is_pinned_clean(metadata: dict[str, Any]) -> bool:
    return (
        metadata.get("tracked_at_log_time") is True
        and metadata.get("working_tree_status") == "clean"
        and isinstance(metadata.get("commit"), str)
        and bool(metadata.get("commit"))
        and isinstance(metadata.get("relative_path"), str)
        and bool(metadata.get("relative_path"))
        and isinstance(metadata.get("remote"), str)
        and normalize_remote(metadata["remote"]) is not None
    )


def _reference_evidence(reference: dict[str, Any], activity_date: str) -> dict[str, str]:
    return {
        "activity_date": activity_date,
        "source": str(reference.get("source", "unknown")),
        "value": str(reference.get("raw", "")),
    }


def _name_for_path(path: str, entry_type: str) -> str:
    if entry_type == "url":
        parsed = urlsplit(path)
        segment = parsed.path.rstrip("/").rsplit("/", 1)[-1]
        return Path(segment).stem if segment else parsed.netloc
    return Path(path).stem


def _repository_for(reference: dict[str, Any], record: dict[str, Any]) -> str | None:
    metadata = reference.get("metadata")
    if isinstance(metadata, dict):
        for key in ("repo_root", "remote"):
            value = metadata.get(key)
            if isinstance(value, str) and value:
                return value
    for key in ("project_path", "project_name"):
        value = record.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def classify_reference(
    reference: dict[str, Any], record: dict[str, Any], activity_date: str
) -> dict[str, Any]:
    """Classify one explicit reference without reading or fetching its content."""

    raw = str(reference.get("raw", ""))
    metadata = reference.get("metadata")
    metadata = metadata if isinstance(metadata, dict) else {}
    evidence = [_reference_evidence(reference, activity_date)]
    repository = _repository_for(reference, record)

    if urlsplit(raw).scheme:
        normalized_url = _normalize_url(raw)
        if normalized_url is None:
            raise AnalyzerError(f"unsupported reference URL: {raw}")
        return {
            "status": "active",
            "type": "url",
            "path": normalized_url,
            "name": _name_for_path(normalized_url, "url"),
            "repo": repository,
            "evidence": evidence,
            "reason": "Referenced HTTPS document URL is available without a network request",
        }

    local_path = (
        _resolve_structured_path(reference, record)
        if metadata
        else resolve_legacy_path(raw, record)
    )
    display_path = str(local_path) if local_path is not None else raw
    if local_path is not None and local_path.exists() and local_path.is_file():
        return {
            "status": "active",
            "type": "doc",
            "path": display_path,
            "name": _name_for_path(display_path, "doc"),
            "repo": repository,
            "evidence": evidence,
            "reason": "Referenced local document exists",
        }

    if not local_path and metadata:
        display_path = str(metadata.get("path") or raw)
    if _metadata_is_pinned_clean(metadata):
        pinned_url = build_pinned_url(
            metadata["remote"], metadata["commit"], metadata["relative_path"]
        )
        if pinned_url:
            return {
                "status": "stale-worktree",
                "type": "url",
                "path": pinned_url,
                "name": _name_for_path(pinned_url, "url"),
                "repo": repository,
                "evidence": evidence,
                "reason": "Deleted local worktree recovered as a commit-pinned URL",
            }

    return {
        "status": "unresolved",
        "type": "doc",
        "path": display_path,
        "name": _name_for_path(display_path, "doc"),
        "repo": repository,
        "evidence": evidence,
        "reason": "Local document is missing and no reliable pinned URL is available",
    }


def _map_key(entry_type: str, path: str) -> tuple[str, str] | None:
    if entry_type in {"doc", "repo"}:
        try:
            return "local", str(Path(path).expanduser().resolve(strict=False))
        except (OSError, RuntimeError, ValueError):
            return None
    normalized = _normalize_url(path)
    return ("url", normalized) if normalized else None


def load_map_keys(map_path: Path) -> set[tuple[str, str]]:
    if YAML_IMPORT_ERROR is not None or yaml is None:
        raise AnalyzerError(f"PyYAML is required to parse repos.yaml: {YAML_IMPORT_ERROR}")
    try:
        raw = yaml.safe_load(map_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise AnalyzerError(f"repos.yaml cannot be read or parsed: {exc}") from exc
    if not isinstance(raw, dict) or not isinstance(raw.get("repos"), list):
        raise AnalyzerError("repos.yaml must contain a list-valued repos field")
    keys: set[tuple[str, str]] = set()
    for index, item in enumerate(raw["repos"]):
        if not isinstance(item, dict) or not all(
            isinstance(item.get(field), str) for field in ("name", "type", "path")
        ):
            raise AnalyzerError(f"repos.yaml entry #{index} is malformed")
        if item["type"] not in SUPPORTED_ENTRY_TYPES:
            raise AnalyzerError(f"repos.yaml entry #{index} has unsupported type")
        key = _map_key(item["type"], item["path"])
        if key is None:
            raise AnalyzerError(f"repos.yaml entry #{index} has an invalid path")
        keys.add(key)
    return keys


def _find_git_root(cwd: Path) -> Path:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = getattr(exc, "stderr", "") or str(exc)
        raise AnalyzerError(f"cannot find current Git root for default map: {detail.strip()}") from exc
    return Path(result.stdout.strip()).resolve()


def _resolved_range(since_value: str | None, until_value: str | None) -> tuple[date, date]:
    today = datetime.now(timezone.utc).date()
    try:
        until = date.fromisoformat(until_value) if until_value else today
        since = date.fromisoformat(since_value) if since_value else until - timedelta(days=30)
    except ValueError as exc:
        raise AnalyzerError("dates must use YYYY-MM-DD") from exc
    if since > until:
        raise AnalyzerError("--since cannot be after --until")
    return since, until


def _date_datetime(value: date) -> datetime:
    return datetime.combine(value, time.min, tzinfo=timezone.utc)


def _merge_result(collection: dict[tuple[str, str], dict[str, Any]], result: dict[str, Any]) -> None:
    key = _map_key(result["type"], result["path"])
    if key is None:
        key = (result["type"], result["path"])
    existing = collection.get(key)
    if existing is None:
        collection[key] = result
        return
    existing_evidence = existing.setdefault("evidence", [])
    for evidence in result.get("evidence", []):
        if evidence not in existing_evidence:
            existing_evidence.append(evidence)


def analyze_references(
    activities_dir: Path,
    map_path: Path,
    since: date,
    until: date,
) -> tuple[dict[str, Any], int]:
    """Return report payload and count of valid records in the selected range."""

    mapped_keys = load_map_keys(map_path)
    candidate_results: dict[tuple[str, str], dict[str, Any]] = {}
    unresolved_results: dict[tuple[str, str], dict[str, Any]] = {}
    mapped_results: dict[tuple[str, str], dict[str, Any]] = {}
    record_count = 0

    for record_path, record in iter_activity_records(
        activities_dir, _date_datetime(since), _date_datetime(until)
    ):
        record_count += 1
        timestamp = _parse_timestamp(record.get("timestamp"))
        activity_date = timestamp.date().isoformat() if timestamp else "unknown"
        references = list(iter_structured_references(record))
        references.extend(iter_legacy_paths(record))
        for reference in references:
            reference["source"] = f"{record_path.name}:{reference['source']}"
            result = classify_reference(reference, record, activity_date)
            if result["status"] == "unresolved":
                _merge_result(unresolved_results, result)
                continue
            key = _map_key(result["type"], result["path"])
            if key in mapped_keys:
                result["status"] = "already-mapped"
                result["reason"] = "Exact normalized path already exists in repos.yaml"
                _merge_result(mapped_results, result)
            else:
                _merge_result(candidate_results, result)

    payload = {
        "since": f"{since.isoformat()}T00:00:00Z",
        "until": f"{until.isoformat()}T00:00:00Z",
        "candidates": sorted(
            candidate_results.values(), key=lambda item: (item["path"], item["type"])
        ),
        "unresolved": sorted(
            unresolved_results.values(), key=lambda item: (item["path"], item["type"])
        ),
        "already_mapped": sorted(
            mapped_results.values(), key=lambda item: (item["path"], item["type"])
        ),
    }
    return payload, record_count


def _evidence_text(item: dict[str, Any]) -> str:
    evidence = item.get("evidence", [])
    if not isinstance(evidence, list):
        return ""
    return "; ".join(
        f"{entry.get('activity_date', 'unknown')} {entry.get('source', 'unknown')}"
        for entry in evidence
        if isinstance(entry, dict)
    )


def render_markdown(payload: dict[str, Any], record_count: int) -> str:
    lines = [
        "# Referenced Documents Audit",
        "",
        f"Range: `{payload['since']}` through `{payload['until']}` (UTC)",
        f"Activity records matched: `{record_count}`",
        "",
    ]
    if record_count == 0:
        lines.extend(
            [
                f"No activity records matched the exact range `{payload['since']}` through `{payload['until']}`.",
                "",
            ]
        )

    sections = (
        ("Candidates", payload["candidates"]),
        ("Unresolved", payload["unresolved"]),
        ("Already mapped", payload["already_mapped"]),
    )
    for title, items in sections:
        lines.extend([f"## {title}", ""])
        if not items:
            lines.extend(["- None", ""])
            continue
        for item in items:
            lines.extend(
                [
                    f"- `{item['status']}` `{item['type']}` `{item['path']}`",
                    f"  - name: `{item['name']}`",
                    f"  - repository: `{item['repo'] or 'unknown'}`",
                    f"  - evidence: `{_evidence_text(item) or 'unknown'}`",
                    f"  - reason: {item['reason']}",
                ]
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Find explicitly referenced documents missing from session-start/repos.yaml"
    )
    parser.add_argument("--activities-dir", type=Path)
    parser.add_argument("--map", dest="map_path", type=Path)
    parser.add_argument("--since")
    parser.add_argument("--until")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if YAML_IMPORT_ERROR is not None or yaml is None:
            raise AnalyzerError(
                f"PyYAML is required before producing candidates: {YAML_IMPORT_ERROR}"
            )
        since, until = _resolved_range(args.since, args.until)
        activities_dir = args.activities_dir or Path(
            os.environ.get("CLAUDE_ACTIVITIES_DIR", str(Path.home() / ".claude/activities"))
        )
        map_path = args.map_path.expanduser() if args.map_path else None
        if map_path is None:
            map_path = _find_git_root(Path.cwd()) / ".claude/skills/session-start/repos.yaml"
        if not map_path.is_file():
            raise AnalyzerError(f"repos.yaml is missing: {map_path}")
        payload, record_count = analyze_references(
            activities_dir.expanduser(), map_path, since, until
        )
    except AnalyzerError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(render_markdown(payload, record_count), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
