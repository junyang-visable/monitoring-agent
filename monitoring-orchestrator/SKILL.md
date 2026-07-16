# Monitoring Agent Skill

Orchestrate real monitoring capabilities for every enabled project in `monitoring-orchestrator/config/monitoring_config.yaml`.

## Required sequence

1. Parse and validate the configuration.
2. For each enabled project, start the four signal paths in parallel.
3. Apply the per-path timeout and capture call metadata.
4. Normalize every response to the contract in `references/contracts.md`.
5. Convert exceptions, missing credentials, permission errors, empty responses, and timeouts into `degraded` or `unavailable` results.
6. Continue other paths after an individual failure.
7. Write one Markdown and one JSON report for the run.
8. Write one redacted evidence JSON file per project and signal.

## Real capability calls

- Datadog → invoke the configured `user-datadog` MCP capability for metrics, monitors, and events.
- Stability SDK → invoke the complete `fe-stability-analysis` sub-skill chain with the rolling `now-24h..now` window.
- Sentry → call the Sentry REST API using the configured organization, project, and time windows.
- tracking_patrol → read the latest GitHub Actions run by default; dispatch a new run only when mode is `trigger` or a manual override requests it.

The Sentry and GitHub HTTP implementations are in `monitoring-orchestrator/runtime.py`. They use only the Python standard library and environment-provided tokens. The Datadog and Stability SDK calls remain capability invocations performed by the agent runtime.

Do not replace any real call with sample data. If a capability cannot be invoked in the current runtime, record that fact as an unavailable result.

## Output

- Markdown template → `monitoring-orchestrator/templates/monitoring_report.md.tpl`
- Thresholds → `monitoring-orchestrator/config/thresholds.yaml`
- Evidence → `artifacts/monitoring/<timestamp>/<project>/<signal>.json`
- Reports → `artifacts/monitoring/<timestamp>/monitoring_report_<timestamp>.md` and `.json`
