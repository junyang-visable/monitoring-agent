"""Shared runtime helpers used by platform adapters."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def _load_dotenv() -> None:
    """Load the first project-root .env without overriding explicit environment vars."""
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
                if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                    value = value[1:-1]
                if key and key not in os.environ:
                    os.environ[key] = value
            break


_load_dotenv()


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "[REDACTED]" if any(token in key.lower() for token in ("token", "secret", "authorization", "password", "api_key", "application_key")) else redact(item)
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
        elif preset == "previous_week":
            this_week = today - timedelta(days=today.weekday())
            start = this_week - timedelta(days=7)
            end = this_week
            label = "previous_week"
        else:
            match = re.fullmatch(r"last_(\d+)([dh])", preset)
            if not match or int(match.group(1)) < 1:
                raise ValueError(
                    "time_range must be today, yesterday, previous_week, "
                    "last_<N>d, last_<N>h, or a {start, end} mapping"
                )
            amount, unit = int(match.group(1)), match.group(2)
            if unit == "h":
                end = current
                start = end - timedelta(hours=amount)
            else:
                start = today - timedelta(days=amount - 1)
                end = current
            label = preset

    if end <= start:
        raise ValueError("time_range.end must be later than time_range.start")
    return {"label": label, "start": start, "end": end}


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


def write_evidence(path: str | Path, result: dict[str, Any]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(redact(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
