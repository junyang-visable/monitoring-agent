"""Backward-compatible runtime facade.

New code should import platform adapters from ``adapters`` directly. The
re-exports below preserve the original ``runtime`` import surface.
"""

from adapters.common import error_result, fetch_json, iso_now, redact, resolve_time_range, write_evidence
from adapters.datadog import fetch_datadog, fetch_datadog_json
from adapters.github import fetch_tracking_patrol
from adapters.sentry import fetch_sentry

__all__ = [
    "error_result",
    "fetch_datadog",
    "fetch_datadog_json",
    "fetch_json",
    "fetch_sentry",
    "fetch_tracking_patrol",
    "iso_now",
    "redact",
    "resolve_time_range",
    "write_evidence",
]
