"""Cover the report formats and Git range checks used by PR secret scanning."""

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.scan_pr_secrets import (
    ScanFailure,
    _scrub,
    parse_gitleaks_report,
    parse_trufflehog_report,
    resolve_scan_range,
)


class ScanPrSecretsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write_report(self, name, content):
        path = self.root / name
        path.write_text(content, encoding="utf-8")
        return path

    def test_gitleaks_accepts_null_and_empty_array_reports(self):
        for content in ("null", "[]"):
            with self.subTest(content=content):
                report = parse_gitleaks_report(self.write_report("gitleaks.json", content))
                self.assertEqual(report.findings, ())
                self.assertEqual(report.candidate_values, ())

    def test_gitleaks_parses_finding_and_normalizes_zero_line(self):
        commit = "a" * 40
        entry = {
            "RuleID": "synthetic-rule",
            "File": "fixtures/example.txt",
            "StartLine": 17,
            "Commit": commit,
            "Secret": "fixture-fixture-fixture",
            "Match": "match-match-match",
        }
        report = parse_gitleaks_report(
            self.write_report("gitleaks.json", json.dumps([entry]))
        )
        self.assertEqual(len(report.findings), 1)
        self.assertEqual(report.findings[0].line, 17)
        self.assertEqual(report.findings[0].commit, commit)
        self.assertEqual(
            report.candidate_values,
            ("fixture-fixture-fixture", "match-match-match"),
        )

        entry["StartLine"] = 0
        zero_line = parse_gitleaks_report(
            self.write_report("gitleaks-zero.json", json.dumps([entry]))
        )
        self.assertIsNone(zero_line.findings[0].line)

    def test_trufflehog_parses_jsonl_and_line_metadata(self):
        commit = "b" * 40
        entries = [
            {
                "DetectorName": "synthetic-detector",
                "SourceMetadata": {
                    "Data": {
                        "Git": {
                            "file": "fixtures/first.txt",
                            "line": 23,
                            "commit": commit,
                        }
                    }
                },
                "Raw": "fixture-fixture-fixture",
                "RawV2": "fixture-fixture-two",
                "SecretParts": {"part": "part-part"},
            },
            {
                "DetectorName": "synthetic-detector-two",
                "SourceMetadata": {
                    "Data": {
                        "Git": {
                            "file": "fixtures/second.txt",
                            "line": None,
                            "commit": commit,
                        }
                    }
                },
                "Raw": "",
                "RawV2": "",
            },
        ]
        report = parse_trufflehog_report(
            self.write_report(
                "trufflehog.jsonl",
                "\n".join(json.dumps(entry) for entry in entries) + "\n",
            )
        )
        self.assertEqual(len(report.findings), 2)
        self.assertEqual(report.findings[0].line, 23)
        self.assertIsNone(report.findings[1].line)
        self.assertEqual(report.findings[0].file, "fixtures/first.txt")
        self.assertEqual(
            report.candidate_values,
            (
                "fixture-fixture-fixture",
                "fixture-fixture-two",
                "part-part",
            ),
        )

    def test_scrub_replaces_longer_overlapping_candidate_first(self):
        result = _scrub(
            "path/fixture-fixture-suffix", ("fixture", "fixture-fixture")
        )
        self.assertEqual(result, "path/[REDACTED]-suffix")

    def test_resolve_scan_range_uses_merge_base_and_rejects_empty_range(self):
        self.run_git("init", "--quiet", "--initial-branch=main", cwd=self.root)
        self.run_git("config", "user.name", "Fixture User", cwd=self.root)
        self.run_git("config", "user.email", "fixture@example.invalid", cwd=self.root)
        (self.root / "root.txt").write_text("root\n", encoding="utf-8")
        self.run_git("add", "root.txt", cwd=self.root)
        self.run_git("commit", "--quiet", "-m", "root", cwd=self.root)
        root_commit = self.git_output("rev-parse", "HEAD", cwd=self.root)

        self.run_git("switch", "--quiet", "-c", "base", cwd=self.root)
        (self.root / "base.txt").write_text("base\n", encoding="utf-8")
        self.run_git("add", "base.txt", cwd=self.root)
        self.run_git("commit", "--quiet", "-m", "base", cwd=self.root)
        base_commit = self.git_output("rev-parse", "HEAD", cwd=self.root)

        self.run_git("switch", "--quiet", "-c", "pr", root_commit, cwd=self.root)
        (self.root / "head.txt").write_text("head\n", encoding="utf-8")
        self.run_git("add", "head.txt", cwd=self.root)
        self.run_git("commit", "--quiet", "-m", "PR change", cwd=self.root)
        head_commit = self.git_output("rev-parse", "HEAD", cwd=self.root)

        original_cwd = Path.cwd()
        try:
            os.chdir(self.root)
            merge_base, revision_range = resolve_scan_range(base_commit, head_commit)
            self.assertEqual(merge_base, root_commit)
            self.assertEqual(revision_range, f"{root_commit}..{head_commit}")
            with self.assertRaises(ScanFailure) as raised:
                resolve_scan_range(base_commit, base_commit)
        finally:
            os.chdir(original_cwd)
        self.assertEqual(raised.exception.category, "range_validation")

    @staticmethod
    def run_git(*arguments, cwd):
        subprocess.run(
            ["git", *arguments],
            cwd=cwd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    @staticmethod
    def git_output(*arguments, cwd):
        result = subprocess.run(
            ["git", *arguments],
            cwd=cwd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout.strip()


if __name__ == "__main__":
    unittest.main()
