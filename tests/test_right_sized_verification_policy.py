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
        self.assertIn("L1／L2 先問我 review 要在哪裡跑（這個 session、subagent、新 session", text)
        self.assertIn("再呼叫一次 `code-review-codex`", text)
        self.assertIn("L2 另外跑完整 `completion-gate`", text)
        self.assertNotIn("MUST 先主動呼叫 `code-review-codex`", text)

    def test_claude_policy_routes_review_by_tier(self) -> None:
        text = self.read("global/CLAUDE.md")

        self.assertIn("L0 只做 deterministic checks，不呼叫 native reviewer", text)
        self.assertIn("L1／L2 先問我 review 要在哪裡跑（這個 session、subagent、新 session", text)
        self.assertIn("再呼叫一次 `code-review-claude`", text)
        self.assertIn("OMP 使用同一個 `code-review-claude` mapping", text)
        self.assertIn("L2 另外跑完整 `completion-gate`", text)
        self.assertNotIn("MUST 先主動調用 `code-review-claude`", text)


    def test_l1_l2_commit_review_asks_where_it_runs(self) -> None:
        gate = self.read("completion-gate/SKILL.md")
        self.assertIn("### Review choice at L1 and L2", gate)
        for option in ("**This session**", "**Subagent**", "**New session**"):
            with self.subTest(option=option):
                self.assertIn(option, gate)
        self.assertIn("At L0, do not ask", gate)

        claude = self.read("code-review-claude/SKILL.md")
        self.assertNotIn("Auto-select (c) silently", claude)
        self.assertIn("claude 'Use the quality-gates:code-review-claude skill", claude)
        self.assertIn("earlier in this commit flow", claude)
        self.assertNotIn("silently prepends", self.read("code-review-claude/README.md"))

        codex = self.read("code-review-codex/SKILL.md")
        self.assertNotIn("continue with that label instead of asking", codex)
        self.assertIn("codex 'Use the quality-gates:code-review-codex skill", codex)
        self.assertIn("earlier in this commit flow", codex)
        self.assertNotIn("in this turn", claude + codex)
        self.assertLess(gate.index("**New session**"), gate.index("**This session**"))
        self.assertIn("List it only when this runtime exposes a subagent", codex)


if __name__ == "__main__":
    unittest.main()
