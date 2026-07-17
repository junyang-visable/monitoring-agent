---
name: monitoring-orchestrator
description: Orchestrate real multi-project frontend monitoring across Datadog, Stability SDK, Sentry, and GitHub Actions. Use for manual or scheduled monitoring runs, shared time-range queries, normalized evidence, and monitoring reports.
---

# Monitoring Orchestrator

Orchestrate real monitoring capabilities for every enabled project in `monitoring-orchestrator/config/monitoring_config.yaml`.

## Required sequence

1. Parse and validate the configuration.
2. Resolve `time_range`, using a project value when present or `defaults.time_range` otherwise. A manual request may override it for this run only.
3. Start Datadog, Sentry, and tracking patrol paths in parallel for each enabled project.
4. Start one shared Stability SDK path for all enabled Stability projects: invoke `fe-stability-analysis` once with sorted standard `app_names`, the resolved time intent, `output_mode=analysis_only`, and `output_dir=artifacts/fe-stability-analysis/<run_id>/`; use its project JSON path mapping to attach each project's Stability result.
5. Apply the per-path timeout and capture call metadata.
6. Normalize every response to the contract in `references/contracts.md`.
7. Convert exceptions, missing credentials, permission errors, empty responses, and timeouts into `degraded` or `unavailable` results.
8. Continue other paths after an individual failure.
9. Write one Markdown and one JSON report for the run.
10. Write one redacted evidence JSON file per project and signal.

## Real capability calls

- Datadog → invoke the configured `user-datadog` MCP capability for metrics, monitors, and events. Pass the resolved UTC `start` and `end`; resolve the filter service as `datadog.service` when configured, otherwise use the project's `app_name`.
- Stability SDK → invoke `fe-stability-analysis` once per monitoring run with the enabled projects' standard `app_names`, resolved `time_range`, `stability_sdk.time_granularity`, `partition_timezone`, `stability_window_hours`, `output_mode=analysis_only`, and `output_dir=artifacts/fe-stability-analysis/<run_id>/`. For `time_granularity=hour`, the SDK queries completed `ds/hh` partitions in the configured partition timezone. Consume each project's dedicated JSON without generating a separate Stability Markdown report.
- Sentry → call the Sentry REST API using the configured organization, project, and resolved window. Use the immediately preceding, equal-duration window as the baseline.
- tracking_patrol → read the latest GitHub Actions run by default; dispatch a new run only when mode is `trigger` or a manual override requests it.

The Sentry and GitHub HTTP implementations are in `monitoring-orchestrator/runtime.py`. They use only the Python standard library and environment-provided tokens. The Datadog and Stability SDK calls remain capability invocations performed by the agent runtime.

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
- Thresholds → `monitoring-orchestrator/config/thresholds.yaml`
- Evidence → `artifacts/monitoring/<timestamp>/<project>/<signal>.json`
- Stability overview → `artifacts/fe-stability-analysis/<run_id>/overview.json`
- Stability projects → `artifacts/fe-stability-analysis/<run_id>/{app_name}.json`
- Reports → `artifacts/monitoring/<timestamp>/report.md` and `report.json`
