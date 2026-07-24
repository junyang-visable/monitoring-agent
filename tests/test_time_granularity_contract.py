"""Regression checks for intent-driven Stability SDK time granularity."""

from pathlib import Path
from datetime import datetime, timezone
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "monitoring-orchestrator"))

from adapters.common import resolve_time_range  # noqa: E402


class TimeGranularityContractTest(unittest.TestCase):
    def test_monitoring_config_uses_automatic_granularity(self) -> None:
        config = (REPO_ROOT / "monitoring-orchestrator/config/monitoring_config.yaml").read_text(encoding="utf-8")
        self.assertIn("  time_granularity: auto", config)

    def test_orchestrator_reserves_hour_mode_for_hour_intents(self) -> None:
        skill = (REPO_ROOT / "monitoring-orchestrator/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("`yesterday` → `day`", skill)
        self.assertIn("`last_<N>h` → `hour`", skill)
        self.assertIn("must not force hour granularity for a day-based intent", skill)
        self.assertIn("Datadog and Sentry keep the exact rolling bounds", skill)
        self.assertIn("Stability independently floors", skill)

    def test_stability_query_defines_yesterday_and_hour_examples(self) -> None:
        skill = (REPO_ROOT / ".agents/skills/fe-stability-query/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("`yesterday` / 昨天", skill)
        self.assertIn("`last_2h`", skill)
        self.assertIn("`last_24h`", skill)
        self.assertIn("所有其他自然日意图", skill)

    def test_http_signal_hour_ranges_keep_rolling_boundaries(self) -> None:
        now = datetime(2026, 7, 24, 6, 12, tzinfo=timezone.utc)

        last_two = resolve_time_range("last_2h", now=now)
        last_twenty_four = resolve_time_range("last_24h", now=now)

        self.assertEqual(last_two["start"], datetime(2026, 7, 24, 4, 12, tzinfo=timezone.utc))
        self.assertEqual(last_two["end"], datetime(2026, 7, 24, 6, 12, tzinfo=timezone.utc))
        self.assertEqual(last_twenty_four["start"], datetime(2026, 7, 23, 6, 12, tzinfo=timezone.utc))
        self.assertEqual(last_twenty_four["end"], datetime(2026, 7, 24, 6, 12, tzinfo=timezone.utc))

    def test_yesterday_uses_the_previous_utc_calendar_day(self) -> None:
        now = datetime(2026, 7, 24, 6, 12, tzinfo=timezone.utc)
        yesterday = resolve_time_range("yesterday", now=now)

        self.assertEqual(yesterday["start"], datetime(2026, 7, 23, 0, 0, tzinfo=timezone.utc))
        self.assertEqual(yesterday["end"], datetime(2026, 7, 24, 0, 0, tzinfo=timezone.utc))


if __name__ == "__main__":
    unittest.main()
