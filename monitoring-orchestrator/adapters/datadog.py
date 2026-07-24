"""Datadog REST API adapter."""

from __future__ import annotations

import json
import os
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .common import error_result, iso_now, resolve_time_range


def fetch_datadog_json(
    url: str,
    api_key: str,
    application_key: str,
    *,
    method: str = "GET",
    params: dict[str, Any] | None = None,
    body: dict[str, Any] | None = None,
    timeout: int = 60,
) -> Any:
    """Call a Datadog API endpoint with API and application key headers."""
    query = urlencode({key: value for key, value in (params or {}).items() if value is not None})
    target = f"{url}?{query}" if query else url
    headers = {"Accept": "application/json", "DD-API-KEY": api_key, "DD-APPLICATION-KEY": application_key}
    data = json.dumps(body).encode() if body is not None else None
    if body is not None:
        headers["Content-Type"] = "application/json"
    request = Request(target, data=data, headers=headers, method=method)
    with urlopen(request, timeout=timeout) as response:
        payload = response.read()
        return json.loads(payload.decode()) if payload else {}


def _latest_points(response: Any) -> list[float]:
    values: list[float] = []
    for series in response.get("series", []) if isinstance(response, dict) else []:
        points = series.get("pointlist", []) if isinstance(series, dict) else []
        numeric = [point[1] for point in points if isinstance(point, list) and len(point) > 1 and isinstance(point[1], (int, float))]
        if numeric:
            values.append(float(numeric[-1]))
    return values


def _error_message(log: dict[str, Any]) -> str:
    attributes = log.get("attributes", {}) if isinstance(log, dict) else {}
    for key in ("message", "error.message", "error", "title"):
        value = attributes.get(key)
        if value:
            return str(value)
    return "unknown"


def fetch_datadog(project_name: str, config: dict[str, Any], timeout: int = 60, time_range: str | dict[str, str] | None = None) -> dict[str, Any]:
    """Fetch Datadog logs, monitors, and configured metric queries over a window."""
    started = time.monotonic()
    api_config = config.get("api", {})
    api_key = os.getenv(api_config.get("api_key_env", "DD_API_KEY"))
    application_key = os.getenv(api_config.get("application_key_env", "DD_APPLICATION_KEY"))
    if not api_key or not application_key:
        missing = [
            name
            for name, value in ((api_config.get("api_key_env", "DD_API_KEY"), api_key), (api_config.get("application_key_env", "DD_APPLICATION_KEY"), application_key))
            if not value
        ]
        return error_result("datadog", project_name, "missing_credential", ", ".join(missing))

    base = api_config.get("base_url", "https://api.datadoghq.com").rstrip("/")
    service = config.get("service") or project_name
    try:
        resolved_range = resolve_time_range(time_range if time_range is not None else config.get("time_range"))
        start, end = resolved_range["start"], resolved_range["end"]
        log_query = str(api_config.get("log_query", "service:{service} status:error")).replace("{service}", service)
        logs_response = fetch_datadog_json(
            f"{base}/api/v2/logs/events/search",
            api_key,
            application_key,
            method="POST",
            body={
                "filter": {"query": log_query, "from": start.isoformat(), "to": end.isoformat(), "indexes": api_config.get("log_indexes", ["*"])},
                "sort": "timestamp",
                "page": {"limit": int(api_config.get("log_limit", 100))},
            },
            timeout=timeout,
        )
        logs = logs_response.get("data", []) if isinstance(logs_response, dict) else []
        message_counts: dict[str, int] = {}
        for log in logs:
            message = _error_message(log)
            message_counts[message] = message_counts.get(message, 0) + 1
        dominant_error = max(message_counts, key=message_counts.get) if message_counts else None

        monitors = fetch_datadog_json(
            f"{base}/api/v1/monitor",
            api_key,
            application_key,
            params={"monitor_tags": f"service:{service}", "with_downtimes": "true"},
            timeout=timeout,
        )
        monitor_rows = [
            {"name": item.get("name"), "state": item.get("overall_state"), "threshold": item.get("options", {}).get("thresholds")}
            for item in monitors
            if isinstance(item, dict)
        ] if isinstance(monitors, list) else []

        query_results: dict[str, Any] = {}
        query_errors: list[dict[str, str]] = []
        for name, query_template in api_config.get("metric_queries", {}).items():
            if not query_template:
                continue
            query = str(query_template).replace("{service}", service)
            try:
                result = fetch_datadog_json(
                    f"{base}/api/v1/query",
                    api_key,
                    application_key,
                    params={"from": int(start.timestamp()), "to": int(end.timestamp()), "query": query},
                    timeout=timeout,
                )
                points = _latest_points(result)
                query_results[name] = {"query": query, "latest_values": points, "series_count": len(points)}
            except (HTTPError, URLError, ValueError, json.JSONDecodeError) as exc:
                query_errors.append({"type": type(exc).__name__, "message": f"{name}: {exc}"})

        metrics = {
            "error_log_count": len(logs),
            "error_log_sample_size": len(logs),
            "dominant_error": dominant_error,
            "monitors": monitor_rows,
            "metric_queries": query_results,
            "time_range": {"label": resolved_range["label"], "start": start.isoformat(), "end": end.isoformat()},
        }
        return {
            "signal": "datadog",
            "project": project_name,
            "status": "degraded" if query_errors else "ok",
            "observed_at": iso_now(),
            "duration_ms": round((time.monotonic() - started) * 1000),
            "summary": f"{len(logs)} error logs sampled and {len(monitor_rows)} monitors found in {resolved_range['label']}",
            "metrics": metrics,
            "errors": query_errors,
            "evidence": "",
        }
    except (HTTPError, URLError, KeyError, ValueError, json.JSONDecodeError) as exc:
        return error_result("datadog", project_name, type(exc).__name__, str(exc), round((time.monotonic() - started) * 1000))

