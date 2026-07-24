"""Tests for Datadog log aggregation behavior."""

from pathlib import Path
import os
import sys
import unittest
from unittest.mock import patch


ORCHESTRATOR_ROOT = Path(__file__).resolve().parents[1] / "monitoring-orchestrator"
sys.path.insert(0, str(ORCHESTRATOR_ROOT))

from adapters import datadog  # noqa: E402


class DatadogAggregationTest(unittest.TestCase):
    def test_returns_total_errors_and_top_five_error_groups(self) -> None:
        requests: list[tuple[str, dict]] = []

        def fake_fetch(url: str, api_key: str, application_key: str, **kwargs):
            requests.append((url, kwargs))
            body = kwargs.get("body", {})
            if url.endswith("/api/v2/logs/analytics/aggregate"):
                if body.get("group_by"):
                    return {
                        "data": {
                            "buckets": [
                                {"by": {"@error.message": "boom"}, "computes": {"c0": 20}},
                                {"by": {"@error.message": "timeout"}, "computes": {"c0": 12}},
                            ]
                        }
                    }
                return {"data": {"buckets": [{"computes": {"c0": 42}}]}}
            if url.endswith("/api/v1/monitor"):
                return []
            raise AssertionError(f"Unexpected URL: {url}")

        config = {
            "service": "visable-dev/search-frontend",
            "api": {
                "api_key_env": "TEST_DD_API_KEY",
                "application_key_env": "TEST_DD_APPLICATION_KEY",
                "error_group_by": "@error.message",
                "top_error_limit": 5,
            },
        }

        with (
            patch.dict(os.environ, {"TEST_DD_API_KEY": "api", "TEST_DD_APPLICATION_KEY": "app"}),
            patch.object(datadog, "fetch_datadog_json", side_effect=fake_fetch),
        ):
            result = datadog.fetch_datadog(
                "search-frontend",
                config,
                time_range={"start": "2026-07-23T00:00:00Z", "end": "2026-07-24T00:00:00Z"},
            )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["metrics"]["error_log_count"], 42)
        self.assertEqual(
            result["metrics"]["top_errors"],
            [
                {"rank": 1, "error": "boom", "count": 20},
                {"rank": 2, "error": "timeout", "count": 12},
            ],
        )
        aggregate_requests = [kwargs["body"] for url, kwargs in requests if url.endswith("/api/v2/logs/analytics/aggregate")]
        self.assertEqual(len(aggregate_requests), 2)
        self.assertEqual(aggregate_requests[1]["group_by"][0]["limit"], 5)
        self.assertEqual(aggregate_requests[1]["group_by"][0]["facet"], "@error.message")
        self.assertEqual(aggregate_requests[1]["group_by"][0]["sort"]["order"], "desc")


if __name__ == "__main__":
    unittest.main()
