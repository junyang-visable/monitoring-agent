"""GitHub Actions adapter for tracking patrol."""

from __future__ import annotations

import os
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from typing import Any

from .common import error_result, fetch_json, iso_now


def fetch_tracking_patrol(project_name: str, config: dict[str, Any], mode: str | None = None, timeout: int = 60) -> dict[str, Any]:
    started = time.monotonic()
    resolved_mode = mode or config.get("mode", "read_latest")
    token = os.getenv(config.get("token_env", "GITHUB_TOKEN"))
    if not token:
        return error_result("tracking_patrol", project_name, "missing_credential", config.get("token_env", "GITHUB_TOKEN"))
    owner, repo, workflow = config["owner"], config["repository"], config["workflow"]
    try:
        if resolved_mode == "trigger":
            ref = config.get("ref", "main")
            fetch_json(f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow}/dispatches", token, method="POST", body={"ref": ref}, timeout=timeout)
        query = urlencode({"event": "workflow_dispatch"}) if resolved_mode == "trigger" else ""
        runs = fetch_json(f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow}/runs?per_page=1&{query}", token, timeout=timeout)
        latest = (runs.get("workflow_runs") or [{}])[0]
        if not latest:
            return error_result("tracking_patrol", project_name, "empty_response", "GitHub returned no workflow runs")
        conclusion = latest.get("conclusion") or "in_progress"
        status = "ok" if conclusion == "success" else "degraded"
        return {"signal": "tracking_patrol", "project": project_name, "status": status, "observed_at": iso_now(), "duration_ms": round((time.monotonic() - started) * 1000), "summary": f"latest patrol run: {conclusion}", "metrics": {"run_id": latest.get("id"), "conclusion": conclusion, "html_url": latest.get("html_url")}, "errors": [], "evidence": ""}
    except (HTTPError, URLError, KeyError, ValueError, TypeError) as exc:
        return error_result("tracking_patrol", project_name, type(exc).__name__, str(exc), round((time.monotonic() - started) * 1000))
