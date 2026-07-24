"""Tests for shared platform configuration and project overrides."""

from pathlib import Path
import sys
import unittest


ORCHESTRATOR_ROOT = Path(__file__).resolve().parents[1] / "monitoring-orchestrator"
sys.path.insert(0, str(ORCHESTRATOR_ROOT))

from adapters.config import resolve_project_signal_config  # noqa: E402


class ProjectSignalConfigTest(unittest.TestCase):
    def test_repository_config_keeps_shared_fields_out_of_project_blocks(self) -> None:
        config_text = (ORCHESTRATOR_ROOT / "config/monitoring_config.yaml").read_text(encoding="utf-8")
        search_block = config_text.split("  search-frontend:\n", 1)[1].split("  product-editor-frontend:\n", 1)[0]
        product_block = config_text.split("  product-editor-frontend:\n", 1)[1]

        for shared_setting in (
            '    base_url: "https://api.datadoghq.com"',
            '  organization: "visable-gmbh"',
            '  owner: "visable-dev"',
            '  repository: "cypress-e2e-framework"',
        ):
            self.assertIn(shared_setting, config_text)

        for project_block in (search_block, product_block):
            self.assertNotIn("      api:", project_block)
            self.assertNotIn("      organization:", project_block)
            self.assertNotIn("      owner:", project_block)
            self.assertNotIn("      repository:", project_block)

    def test_project_values_override_shared_values_recursively(self) -> None:
        config = {
            "datadog": {
                "api": {
                    "base_url": "https://api.datadoghq.com",
                    "log_limit": 100,
                    "metric_queries": {"error_rate": None, "p95_latency": None},
                }
            },
            "projects": {
                "product-editor-frontend": {
                    "datadog": {
                        "enabled": True,
                        "service": "visable-dev/product-editor-frontend",
                        "api": {"log_limit": 50},
                    }
                }
            },
        }

        resolved = resolve_project_signal_config(config, "product-editor-frontend", "datadog")

        self.assertTrue(resolved["enabled"])
        self.assertEqual(resolved["service"], "visable-dev/product-editor-frontend")
        self.assertEqual(resolved["api"]["base_url"], "https://api.datadoghq.com")
        self.assertEqual(resolved["api"]["log_limit"], 50)
        self.assertEqual(resolved["api"]["metric_queries"], {"error_rate": None, "p95_latency": None})

    def test_shared_sentry_and_tracking_values_are_inherited(self) -> None:
        config = {
            "sentry": {"organization": "visable-gmbh", "token_env": "SENTRY_AUTH_TOKEN"},
            "tracking_patrol": {"owner": "visable-dev", "repository": "cypress-e2e-framework", "mode": "read_latest"},
            "projects": {
                "search-frontend": {
                    "sentry": {"enabled": True, "project": "search-frontend"},
                    "tracking_patrol": {"enabled": True, "workflow": "team-dolphin-schedule.yml"},
                }
            },
        }

        sentry = resolve_project_signal_config(config, "search-frontend", "sentry")
        patrol = resolve_project_signal_config(config, "search-frontend", "tracking_patrol")

        self.assertEqual(sentry["organization"], "visable-gmbh")
        self.assertEqual(sentry["project"], "search-frontend")
        self.assertEqual(patrol["owner"], "visable-dev")
        self.assertEqual(patrol["workflow"], "team-dolphin-schedule.yml")
        self.assertEqual(patrol["mode"], "read_latest")


if __name__ == "__main__":
    unittest.main()
