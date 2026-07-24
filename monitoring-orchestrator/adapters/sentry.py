"""Sentry REST API adapter."""

from __future__ import annotations

import os
import time
from datetime import datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

from .common import error_result, fetch_json, iso_now, resolve_time_range


def _count(items: list[dict[str, Any]]) -> int:
    return sum(int(item.get("count", 0) or 0) for item in items)


def fetch_sentry(project_name: str, config: dict[str, Any], timeout: int = 60, time_range: str | dict[str, str] | None = None) -> dict[str, Any]:
    started = time.monotonic()
    token = os.getenv(config.get("token_env", "SENTRY_AUTH_TOKEN"))
    if not token:
        return error_result("sentry", project_name, "missing_credential", config.get("token_env", "SENTRY_AUTH_TOKEN"))
    base = config.get("base_url", "https://sentry.io").rstrip("/")
    organization = config["organization"]
    project = config["project"]
    try:
        resolved_range = resolve_time_range(time_range if time_range is not None else config.get("time_range"))
        current_start, end = resolved_range["start"], resolved_range["end"]
        baseline_start = current_start - (end - current_start)

        def count(start: datetime, finish: datetime) -> int:
            query = urlencode({"project": project, "start": start.isoformat(), "end": finish.isoformat(), "limit": 100})
            data = fetch_json(f"{base}/api/0/organizations/{organization}/issues/?{query}", token, timeout=timeout)
            return _count(data if isinstance(data, list) else data.get("issues", []))

        baseline = count(baseline_start, current_start)
        current = count(current_start, end)
        metrics: dict[str, Any] = {
            "current": current,
            "baseline": baseline,
            "delta": current - baseline,
            "windows": {"current": [current_start.isoformat(), end.isoformat()], "baseline": [baseline_start.isoformat(), current_start.isoformat()]},
            "time_range": {"label": resolved_range["label"], "start": current_start.isoformat(), "end": end.isoformat()},
        }
        if baseline:
            metrics["delta_percent"] = round((current - baseline) / baseline * 100, 2)
        return {"signal": "sentry", "project": project_name, "status": "ok", "observed_at": iso_now(), "duration_ms": round((time.monotonic() - started) * 1000), "summary": f"{current} errors in {resolved_range['label']}; delta {current - baseline}", "metrics": metrics, "errors": [], "evidence": ""}
    except (HTTPError, URLError, KeyError, ValueError, TypeError) as exc:
        return error_result("sentry", project_name, type(exc).__name__, str(exc), round((time.monotonic() - started) * 1000))

