---
name: monitoring-orchestrator
description: Orchestrate real multi-project frontend monitoring across Datadog, Stability SDK, Sentry, and GitHub Actions. Use for manual or scheduled monitoring runs, shared time-range queries, normalized evidence, and monitoring reports.
---

# Monitoring Orchestrator

Orchestrate real monitoring capabilities for every enabled project in `monitoring-orchestrator/config/monitoring_config.yaml`.

## Required sequence

1. Parse and validate the configuration. Resolve each project's effective `enabled` value, then build separate eligible-project lists for Datadog, Sentry, and tracking patrol from each signal's project-level `enabled` value. Stability SDK is the exception: its `enabled` value is global and must not be read from a project.
2. Resolve `time_range`, using a project value when present or `defaults.time_range` otherwise. A manual request may override it for this run only.
3. Start Datadog, Sentry, and tracking patrol paths in parallel for their respective eligible-project lists.
4. Generate one UTC `run_id` in `YYYYMMDDTHHMMSSZ` format. Run the shared Stability path only when global `stability_sdk.enabled == true`. When the global switch is false, skip the path entirely: must not invoke `fe-stability-analysis`, must not read its capability specification, and must not create Stability artifacts. When it is true, validate the single root-level `stability_sdk` configuration, build `stability_projects` from all enabled projects, and invoke `fe-stability-analysis` once with their sorted standard `app_names`, the resolved time intent, the global `time_granularity`, `partition_timezone`, `stability_window_hours`, `output_mode=analysis_only`, and `output_dir=artifacts/monitoring/<run_id>/`; use its project JSON path mapping to attach each project's Stability result. If the global switch is true but no projects are enabled, record a configuration error without invoking the skill.
5. Apply the per-path timeout and capture call metadata.
6. Normalize every response to the contract in `references/contracts.md`.
7. Convert exceptions, missing credentials, permission errors, empty responses, and timeouts into `degraded` or `unavailable` results.
8. Continue other paths after an individual failure.
9. Write one Markdown and one JSON report for the run.
10. Write one redacted evidence JSON file per project and signal.

## Real capability calls

- Before each capability call, read its dedicated specification:
  - Datadog → [references/capabilities/datadog.md](references/capabilities/datadog.md)
  - Stability SDK → [references/capabilities/stability-sdk.md](references/capabilities/stability-sdk.md)
  - Sentry → [references/capabilities/sentry.md](references/capabilities/sentry.md)
  - tracking_patrol → [references/capabilities/tracking-patrol.md](references/capabilities/tracking-patrol.md)

The platform HTTP implementations are in `monitoring-orchestrator/adapters/`: `datadog.py`, `sentry.py`, and `github.py`. Shared helpers are in `adapters/common.py`; `runtime.py` remains a backward-compatible import facade. They use only the Python standard library and environment-provided credentials. Stability SDK remains a capability invocation performed by the agent runtime.

Do not replace any real call with sample data. If a capability cannot be invoked in the current runtime, record that fact as an unavailable result.

## Time range

`time_range` is inherited from `defaults` and can be overridden per project or by a manual request. Support `today`, `yesterday`, `last_<N>d` (for example `last_7d`), `last_<N>h` (for example `last_24h`), and an explicit mapping:

```yaml
time_range:
  start: "2026-07-01T00:00:00Z"
  end: "2026-07-08T00:00:00Z"
```

Resolve presets in UTC. `last_<N>d` starts at the beginning of today minus `N - 1` days and ends at the current time, so it includes today; `last_<N>h` is an exact rolling-hour window. Datadog and Sentry receive the exact UTC `start`/`end`. Stability SDK is natural-day data and receives the calendar-day range covering the window, not a false claim of hour precision. Do not apply a time range to `tracking_patrol`; it always reads the latest run unless explicitly triggered.

## Output

- Markdown template → `monitoring-orchestrator/templates/monitoring_report.md.tpl`
- Report formatting rules → `references/report-format.md`
- Signal contract → `references/contracts.md`
- Capability specifications → `references/capabilities/`
- Thresholds → `monitoring-orchestrator/config/thresholds.yaml`
- Evidence → `artifacts/monitoring/<run_id>/<project>/<signal>.json` (`run_id` is UTC `YYYYMMDDTHHMMSSZ`)
- Stability overview → `artifacts/monitoring/<run_id>/overview.json`
- Stability projects → `artifacts/monitoring/<run_id>/{app_name}/fe-stability-analysis.json`
- Reports → `artifacts/monitoring/<run_id>/report.md` and `report.json`

Step 9 (write reports) MUST follow [references/report-format.md](references/report-format.md). The report is a signal-level dashboard; detailed analysis stays in evidence JSONs.
