"""Backward-compatible runtime facade.

New code should import platform adapters from ``adapters`` directly. The
re-exports below preserve the original ``runtime`` import surface.
"""

from adapters.common import error_result, fetch_json, iso_now, redact, resolve_time_range, write_evidence
from adapters.config import deep_merge, resolve_project_signal_config
from adapters.datadog import fetch_datadog, fetch_datadog_json
from adapters.github import fetch_tracking_patrol
from adapters.sentry import fetch_sentry
from report_html import generate_html_report

__all__ = [
    "error_result",
    "deep_merge",
    "fetch_datadog",
    "fetch_datadog_json",
    "fetch_json",
    "fetch_sentry",
    "fetch_tracking_patrol",
    "generate_html_report",
    "iso_now",
    "redact",
    "resolve_project_signal_config",
    "resolve_time_range",
    "write_evidence",
]
