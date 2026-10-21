#!/usr/bin/env python3
"""Scan the commits introduced by a pull request without logging raw findings."""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


_SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")


@dataclass(frozen=True)
class Finding:
    tool: str
    detector: str
    file: str
    line: int | None
    commit: str | None


@dataclass(frozen=True)
class ScanReport:
    findings: tuple[Finding, ...]
    candidate_values: tuple[str, ...]


class ScanFailure(Exception):
    """An error with a safe category that can be logged without source data."""

    def __init__(self, tool: str, category: str) -> None:
        super().__init__()
        self.tool = tool
        self.category = category


def _reject_json_constant(value: str) -> None:
    raise ValueError(value)


def _required_text(value: dict[str, Any], key: str, tool: str) -> str:
    result = value.get(key)
    if not isinstance(result, str) or not result:
        raise ScanFailure(tool, "invalid_report")
    return result


def _optional_line(value: Any, tool: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ScanFailure(tool, "invalid_report")
    return value or None


def _required_commit(value: Any, tool: str) -> str:
    if not isinstance(value, str) or _SHA_RE.fullmatch(value) is None:
        raise ScanFailure(tool, "invalid_report")
    return value


def parse_gitleaks_report(path: Path) -> ScanReport:
    """Parse the pinned Gitleaks JSON format and retain only safe metadata."""
    tool = "Gitleaks"
    try:
        document = json.loads(
            path.read_text(encoding="utf-8"), parse_constant=_reject_json_constant
        )
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError):
        raise ScanFailure(tool, "invalid_report") from None

    # Go's JSON encoder writes a nil findings slice as null when no secrets match.
    if document is None:
        entries: list[Any] = []
    elif isinstance(document, list):
        entries = document
    else:
        raise ScanFailure(tool, "invalid_report")

    findings: list[Finding] = []
    candidates: list[str] = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise ScanFailure(tool, "invalid_report")
        detector = _required_text(entry, "RuleID", tool)
        file_name = _required_text(entry, "File", tool)
        line = _optional_line(entry.get("StartLine"), tool)
        commit = _required_commit(entry.get("Commit"), tool)

        for key in ("Secret", "Match"):
            candidate = entry.get(key)
            if not isinstance(candidate, str):
                raise ScanFailure(tool, "invalid_report")
            if candidate:
                candidates.append(candidate)

        findings.append(Finding(tool, detector, file_name, line, commit))

    return ScanReport(tuple(findings), tuple(candidates))


def parse_trufflehog_report(path: Path) -> ScanReport:
    """Parse TruffleHog JSON Lines while discarding all raw result fields."""
    tool = "TruffleHog"
    findings: list[Finding] = []
    candidates: list[str] = []
    try:
        report_file = path.open("r", encoding="utf-8")
    except (OSError, UnicodeError):
        raise ScanFailure(tool, "invalid_report") from None

    try:
        with report_file:
            for line_text in report_file:
                if not line_text.strip():
                    continue
                try:
                    entry = json.loads(line_text, parse_constant=_reject_json_constant)
                except (ValueError, json.JSONDecodeError):
                    raise ScanFailure(tool, "invalid_report") from None
                if not isinstance(entry, dict):
                    raise ScanFailure(tool, "invalid_report")

                detector = _required_text(entry, "DetectorName", tool)
                metadata = entry.get("SourceMetadata")
                data = metadata.get("Data") if isinstance(metadata, dict) else None
                git_data = data.get("Git") if isinstance(data, dict) else None
                if not isinstance(git_data, dict):
                    raise ScanFailure(tool, "invalid_report")

                file_name = _required_text(git_data, "file", tool)
                line = _optional_line(git_data.get("line"), tool)
                commit = _required_commit(git_data.get("commit"), tool)

                for key in ("Raw", "RawV2"):
                    candidate = entry.get(key)
                    if not isinstance(candidate, str):
                        raise ScanFailure(tool, "invalid_report")
                    if candidate:
                        candidates.append(candidate)

                secret_parts = entry.get("SecretParts")
                if secret_parts is not None:
                    if not isinstance(secret_parts, dict) or any(
                        not isinstance(part, str) for part in secret_parts.values()
                    ):
                        raise ScanFailure(tool, "invalid_report")
                    candidates.extend(part for part in secret_parts.values() if part)

                findings.append(Finding(tool, detector, file_name, line, commit))
    except (OSError, UnicodeError):
        raise ScanFailure(tool, "invalid_report") from None

    return ScanReport(tuple(findings), tuple(candidates))


def _git_command(arguments: list[str]) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            ["git", *arguments],
            check=False,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except OSError:
        raise ScanFailure("git", "range_validation") from None
    if result.returncode != 0:
        raise ScanFailure("git", "range_validation")
    return result


def resolve_scan_range(base_sha: str, head_sha: str) -> tuple[str, str]:
    """Return a nonempty merge-base..head range after validating both commits."""
    if _SHA_RE.fullmatch(base_sha) is None or _SHA_RE.fullmatch(head_sha) is None:
        raise ScanFailure("git", "range_validation")

    def resolve_commit(sha: str) -> str:
        result = _git_command(["rev-parse", "--verify", f"{sha}^{{commit}}"])
        commit = result.stdout.strip()
        if _SHA_RE.fullmatch(commit) is None:
            raise ScanFailure("git", "range_validation")
        return commit

    base_commit = resolve_commit(base_sha)
    head_commit = resolve_commit(head_sha)
    merge_base = _git_command(["merge-base", base_commit, head_commit]).stdout.strip()
    if _SHA_RE.fullmatch(merge_base) is None:
        raise ScanFailure("git", "range_validation")

    ancestor_check = subprocess.run(
        ["git", "merge-base", "--is-ancestor", merge_base, head_commit],
        check=False,
        shell=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if ancestor_check.returncode != 0:
        raise ScanFailure("git", "range_validation")

    revision_range = f"{merge_base}..{head_commit}"
    count_result = _git_command(["rev-list", "--count", revision_range])
    count_text = count_result.stdout.strip()
    if not count_text.isdecimal() or int(count_text) < 1:
        raise ScanFailure("git", "range_validation")
    return merge_base, revision_range


def _emit_error(tool: str, category: str, exit_code: int | None) -> None:
    print(
        json.dumps(
            {
                "type": "error",
                "tool": tool,
                "category": category,
                "exit_code": exit_code,
            },
            ensure_ascii=True,
            separators=(",", ":"),
        )
    )


def _scrub(value: str, candidates: tuple[str, ...]) -> str:
    for candidate in sorted(set(candidates), key=len, reverse=True):
        if candidate:
            value = value.replace(candidate, "[REDACTED]")
    return value


def _emit_findings(
    reports: tuple[ScanReport, ...], candidates: tuple[str, ...]
) -> None:
    for tool, report in zip(("Gitleaks", "TruffleHog"), reports, strict=True):
        print(
            json.dumps(
                {"type": "summary", "tool": tool, "count": len(report.findings)},
                ensure_ascii=True,
                separators=(",", ":"),
            )
        )
        for finding in report.findings:
            record = {
                "type": "finding",
                "tool": finding.tool,
                "detector": _scrub(finding.detector, candidates),
                "file": _scrub(finding.file, candidates),
                "line": finding.line,
                "commit": _scrub(finding.commit or "", candidates) or None,
            }
            print(json.dumps(record, ensure_ascii=True, separators=(",", ":")))


def _binary_path(environment: str, tool: str) -> Path:
    value = os.environ.get(environment)
    if not value:
        raise ScanFailure(tool, "configuration")
    try:
        path = Path(value).resolve(strict=True)
    except OSError:
        raise ScanFailure(tool, "configuration") from None
    if not path.is_file() or not os.access(path, os.X_OK):
        raise ScanFailure(tool, "configuration")
    return path


def _run_scanner(
    tool: str,
    command: list[str],
    stdout_path: Path,
    stderr_path: Path,
) -> subprocess.CompletedProcess[bytes]:
    try:
        with stdout_path.open("wb") as stdout_file, stderr_path.open("wb") as stderr_file:
            return subprocess.run(
                command,
                check=False,
                shell=False,
                stdout=stdout_file,
                stderr=stderr_file,
            )
    except OSError:
        raise ScanFailure(tool, "execution_failed") from None


def main() -> int:
    required = ("BASE_SHA", "HEAD_SHA", "RUNNER_TEMP")
    if any(not os.environ.get(name) for name in required):
        _emit_error("helper", "configuration", None)
        return 1

    try:
        base_sha = os.environ["BASE_SHA"]
        head_sha = os.environ["HEAD_SHA"]
        runner_temp = Path(os.environ["RUNNER_TEMP"]).resolve(strict=True)
        if not runner_temp.is_dir() or not os.access(runner_temp, os.W_OK):
            raise ScanFailure("helper", "configuration")
        gitleaks_bin = _binary_path("GITLEAKS_BIN", "Gitleaks")
        trufflehog_bin = _binary_path("TRUFFLEHOG_BIN", "TruffleHog")
        merge_base, revision_range = resolve_scan_range(base_sha, head_sha)
    except ScanFailure as error:
        _emit_error(error.tool, error.category, None)
        return 1
    except OSError:
        _emit_error("helper", "configuration", None)
        return 1
    except Exception:
        _emit_error("helper", "internal_error", None)
        return 1

    reports: list[ScanReport] = []
    errors: list[tuple[str, str, int | None]] = []
    report_parsing_succeeded = True
    try:
        with tempfile.TemporaryDirectory(
            prefix="pr-secret-scan-", dir=runner_temp
        ) as temp_name:
            temp_dir = Path(temp_name)
            # Keep raw scanner reports private until candidate values are scrubbed.
            temp_dir.chmod(0o700)
            gitleaks_report = temp_dir / "gitleaks.json"
            trufflehog_output = temp_dir / "trufflehog.jsonl"
            scans: tuple[tuple[str, list[str], Path, Callable[[Path], ScanReport]], ...] = (
                (
                    "Gitleaks",
                    [
                        str(gitleaks_bin),
                        "git",
                        "--log-opts",
                        revision_range,
                        "--report-format",
                        "json",
                        "--report-path",
                        str(gitleaks_report),
                    ],
                    gitleaks_report,
                    parse_gitleaks_report,
                ),
                (
                    "TruffleHog",
                    [
                        str(trufflehog_bin),
                        "git",
                        "file://.",
                        "--since-commit",
                        merge_base,
                        "--branch",
                        head_sha,
                        "--json",
                        "--no-verification",
                        "--results=verified,unverified,unknown",
                        "--fail",
                        "--fail-on-scan-errors",
                    ],
                    trufflehog_output,
                    parse_trufflehog_report,
                ),
            )

            for index, (tool, command, report_path, parser) in enumerate(scans):
                stdout_path = (
                    trufflehog_output
                    if tool == "TruffleHog"
                    else temp_dir / "gitleaks.stdout"
                )
                stderr_path = temp_dir / f"scanner-{index}.stderr"
                try:
                    result = _run_scanner(tool, command, stdout_path, stderr_path)
                except ScanFailure as error:
                    errors.append((error.tool, error.category, None))
                    report_parsing_succeeded = False
                    continue

                try:
                    report = parser(report_path)
                except ScanFailure as error:
                    errors.append((error.tool, error.category, result.returncode))
                    report_parsing_succeeded = False
                else:
                    reports.append(report)
                    if result.returncode != 0:
                        errors.append((tool, "scanner_exit", result.returncode))
    except OSError:
        _emit_error("helper", "temporary_storage", None)
        return 1
    except Exception:
        _emit_error("helper", "internal_error", None)
        return 1

    if report_parsing_succeeded and len(reports) == 2:
        candidates = tuple(
            candidate for report in reports for candidate in report.candidate_values
        )
        _emit_findings(tuple(reports), candidates)

    for tool, category, exit_code in errors:
        _emit_error(tool, category, exit_code)

    if errors or any(report.findings for report in reports):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
