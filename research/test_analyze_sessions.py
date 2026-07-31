import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent))

from analyze_sessions import calculate_metrics, completed_rows, recommendation


def session(code: str, success: str = "yes", seconds: str = "4") -> dict[str, str]:
    row = {
        "participant_code": code,
        "confidence_1_5": "4.5",
        "voice_preference": "voice",
    }
    for task in range(1, 6):
        row[f"task_{task}_success"] = success
        row[f"task_{task}_seconds"] = seconds
    return row


class AnalyzeSessionsTests(unittest.TestCase):
    def test_ignores_empty_placeholder_rows(self) -> None:
        rows = [{"participant_code": "P001", "task_1_success": ""}]
        self.assertEqual(completed_rows(rows), [])

    def test_calculates_passing_metrics(self) -> None:
        rows = [session(f"P00{index}") for index in range(1, 6)]
        metrics, warnings = calculate_metrics(rows)
        self.assertFalse(warnings)
        self.assertTrue(all(metric.passes for metric in metrics))
        self.assertIn("cumplen", recommendation(metrics, len(rows)))

    def test_requires_five_participants(self) -> None:
        rows = [session("P001")]
        metrics, _ = calculate_metrics(rows)
        self.assertIn("insuficiente", recommendation(metrics, len(rows)).lower())


if __name__ == "__main__":
    unittest.main()

