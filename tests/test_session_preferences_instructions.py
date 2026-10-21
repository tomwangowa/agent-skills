"""Behavioral contracts for the manual session-preferences activation instructions."""
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "session-preferences" / "SKILL.md"


class SessionPreferencesInstructionsTest(unittest.TestCase):
    def setUp(self):
        self.text = SKILL.read_text(encoding="utf-8")
        self.activation = self.text.split("## Activation", 1)[1].split("## Shared Configuration", 1)[0]
        self.normalized_activation = " ".join(self.activation.split())

    def test_manual_reload_replaces_or_clears_the_previous_language_default(self):
        self.assertIn("Each manual activation replaces any previously loaded response-language default.",
                      self.normalized_activation)
        self.assertIn("If `response_language` is null", self.normalized_activation)
        self.assertIn("Fall back to the existing general language instructions", self.normalized_activation)

    def test_success_acknowledgment_uses_the_effective_language(self):
        self.assertIn("confirm activation once in the effective response language", self.normalized_activation)
        self.assertNotIn("已啟用 session-preferences；本 session 後續回應會套用目前規則。", self.activation)


if __name__ == "__main__":
    unittest.main()
