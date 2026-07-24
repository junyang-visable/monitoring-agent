"""Regression checks for configuration-driven monitoring orchestration."""

from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]


class StabilitySignalEnablementContractTest(unittest.TestCase):
    def test_global_stability_switch_controls_the_analysis_skill(self) -> None:
        required_gate = "global `stability_sdk.enabled == true`"
        required_skip = "must not invoke `fe-stability-analysis`"

        for relative_path in (
            "monitoring-orchestrator/SKILL.md",
            "monitoring-orchestrator/references/capabilities/stability-sdk.md",
        ):
            content = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
            self.assertIn(required_gate, content, relative_path)
            self.assertIn(required_skip, content, relative_path)

        config = (REPO_ROOT / "monitoring-orchestrator/config/monitoring_config.yaml").read_text(encoding="utf-8")
        self.assertRegex(config, r"(?m)^stability_sdk:\n  enabled: (?:true|false)$")
        for setting in (
            "  output_mode: analysis_only",
            "  time_granularity: auto",
            "  partition_timezone: GMT+1",
            "  stability_window_days: 1",
            "  stability_window_hours: 1",
        ):
            self.assertIn(setting, config)
        self.assertNotIn("    stability_sdk:", config)


if __name__ == "__main__":
    unittest.main()
