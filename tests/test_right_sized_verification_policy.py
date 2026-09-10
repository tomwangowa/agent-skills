"""Regression tests for the right-sized commit verification policy."""

from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RightSizedVerificationPolicyTests(unittest.TestCase):
    def read(self, relative_path: str) -> str:
        return (ROOT / relative_path).read_text(encoding="utf-8")

    def test_completion_gate_defines_all_risk_tiers_and_report_fields(self) -> None:
        text = self.read("completion-gate/SKILL.md")

        for marker in ("L0", "L1", "L2", "NOT VERIFIED", "ESCALATED"):
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

        for escalator in (
            "authentication",
            "session state",
            "permissions",
            "data-loss",
            "production configuration",
        ):
            with self.subTest(escalator=escalator):
                self.assertIn(escalator, text)

        self.assertIn("An L1 change without a relevant test or checker escalates to L2.", text)
        self.assertIn("An unresolved native-review concern escalates to L2.", text)
        self.assertIn("Full Gate Function and Adversarial Self-Verification", text)

    def test_codex_policy_routes_review_by_tier(self) -> None:
        text = self.read("global/AGENTS.md")

        self.assertIn("L0 只做 deterministic checks，不呼叫 native reviewer", text)
        self.assertIn("L1／L2 呼叫一次 `code-review-codex`", text)
        self.assertIn("L2 另外跑完整 `completion-gate`", text)
        self.assertNotIn("MUST 先主動呼叫 `code-review-codex`", text)

    def test_claude_policy_routes_review_by_tier(self) -> None:
        text = self.read("global/CLAUDE.md")

        self.assertIn("L0 只做 deterministic checks，不呼叫 native reviewer", text)
        self.assertIn("L1／L2 呼叫一次 `code-review-claude`", text)
        self.assertIn("OMP 使用同一個 `code-review-claude` mapping", text)
        self.assertIn("L2 另外跑完整 `completion-gate`", text)
        self.assertNotIn("MUST 先主動調用 `code-review-claude`", text)


if __name__ == "__main__":
    unittest.main()
