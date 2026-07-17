"""Dependency-free HTTP helpers for the Sentry and GitHub signal paths."""

from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def _load_dotenv() -> None:
    """Read a .env file from the project root and inject unset vars into os.environ.

    Searches upward from this file's directory until it finds a .env, stops at filesystem
    root. Only sets variables that are not already present in the environment, so explicit
    exports always take precedence.
    """
    here = Path(__file__).resolve().parent
    for parent in [here, *here.parents]:
        candidate = parent / ".env"
        if candidate.is_file():
            for line in candidate.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key, value = key.strip(), value.strip()
                # Strip optional surrounding quotes
                if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                    value = value[1:-1]
                if key and key not in os.environ:
                    os.environ[key] = value
            break


_load_dotenv()


STATUSES = {"ok", "degraded", "unavailable"}


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "[REDACTED]" if any(token in key.lower() for token in ("token", "secret", "authorization", "password")) else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _as_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Explicit time_range values must include a timezone")
    return parsed.astimezone(timezone.utc)


def resolve_time_range(value: str | dict[str, str] | None, now: datetime | None = None) -> dict[str, Any]:
    """Resolve the shared monitoring window to UTC start/end timestamps."""
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    today = current.replace(hour=0, minute=0, second=0, microsecond=0)

    if isinstance(value, dict):
        start = _as_utc(value["start"])
        end = _as_utc(value["end"])
        label = f"{start.date().isoformat()} to {end.date().isoformat()}"
    else:
        preset = value or "today"
        if preset == "today":
            start, end, label = today, current, "today"
        elif preset == "yesterday":
            end = today
            start = end - timedelta(days=1)
            label = "yesterday"
        else:
            match = re.fullmatch(r"last_(\d+)([dh])", preset)
            if not match or int(match.group(1)) < 1:
                raise ValueError("time_range must be today, yesterday, last_<N>d, last_<N>h, or a {start, end} mapping")
            amount, unit = int(match.group(1)), match.group(2)
            start = current - timedelta(hours=amount) if unit == "h" else today - timedelta(days=amount - 1)
            end, label = current, preset

    if end <= start:
        raise ValueError("time_range.end must be later than time_range.start")
    return {"label": label, "start": start, "end": end}


def sentry_count(items: list[dict[str, Any]]) -> int:
    return sum(int(item.get("count", 0) or 0) for item in items)


def error_result(signal: str, project: str, error_type: str, message: str, duration_ms: int = 0) -> dict[str, Any]:
    return {
        "signal": signal,
        "project": project,
        "status": "unavailable",
        "observed_at": iso_now(),
        "duration_ms": duration_ms,
        "summary": f"{signal} unavailable: {message}",
        "metrics": {},
        "errors": [{"type": error_type, "message": message}],
        "evidence": "",
    }


def fetch_json(url: str, token: str, *, method: str = "GET", body: dict[str, Any] | None = None, timeout: int = 60) -> Any:
    headers = {"Accept": "application/json", "Authorization": f"Bearer {token}"}
    data = json.dumps(body).encode() if body is not None else None
    if body is not None:
        headers["Content-Type"] = "application/json"
    request = Request(url, data=data, headers=headers, method=method)
    with urlopen(request, timeout=timeout) as response:
        payload = response.read()
        return json.loads(payload.decode()) if payload else {}


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
            return sentry_count(data if isinstance(data, list) else data.get("issues", []))

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
    except (HTTPError, URLError, KeyError, ValueError, json.JSONDecodeError) as exc:
        return error_result("sentry", project_name, type(exc).__name__, str(exc), round((time.monotonic() - started) * 1000))


def fetch_tracking_patrol(project_name: str, config: dict[str, Any], mode: str = "read_latest", timeout: int = 60) -> dict[str, Any]:
    started = time.monotonic()
    token = os.getenv(config.get("token_env", "GITHUB_TOKEN"))
    if not token:
        return error_result("tracking_patrol", project_name, "missing_credential", config.get("token_env", "GITHUB_TOKEN"))
    owner, repo, workflow = config["owner"], config["repository"], config["workflow"]
    try:
        if mode == "trigger":
            ref = config.get("ref", "main")
            fetch_json(f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow}/dispatches", token, method="POST", body={"ref": ref}, timeout=timeout)
        query = urlencode({"event": "workflow_dispatch"}) if mode == "trigger" else ""
        runs = fetch_json(f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow}/runs?per_page=1&{query}", token, timeout=timeout)
        latest = (runs.get("workflow_runs") or [{}])[0]
        if not latest:
            return error_result("tracking_patrol", project_name, "empty_response", "GitHub returned no workflow runs")
        conclusion = latest.get("conclusion") or "in_progress"
        status = "ok" if conclusion == "success" else "degraded" if conclusion in {"in_progress", "queued"} else "degraded"
        return {"signal": "tracking_patrol", "project": project_name, "status": status, "observed_at": iso_now(), "duration_ms": round((time.monotonic() - started) * 1000), "summary": f"latest patrol run: {conclusion}", "metrics": {"run_id": latest.get("id"), "conclusion": conclusion, "html_url": latest.get("html_url")}, "errors": [], "evidence": ""}
    except (HTTPError, URLError, KeyError, ValueError, json.JSONDecodeError) as exc:
        return error_result("tracking_patrol", project_name, type(exc).__name__, str(exc), round((time.monotonic() - started) * 1000))


def write_evidence(path: str | Path, result: dict[str, Any]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(redact(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
