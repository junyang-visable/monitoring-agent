# Monitoring Agent

Configuration-driven monitoring agent for collecting signals from multiple projects and producing structured reports.

## Usage

1. Configure projects in `monitoring-orchestrator/config/monitoring_config.yaml`.
2. Put service tokens in environment variables referenced by the config.
3. Invoke `.agents/monitoring-agent.md` or load `monitoring-orchestrator/SKILL.md`.
4. Inspect reports and redacted evidence under `artifacts/monitoring/`.

The agent performs real calls only. Missing credentials, permissions, empty responses, and timeouts are reported as degraded or unavailable; no synthetic metrics are generated.

For Datadog, the agent uses the Datadog REST API with `DD_API_KEY` and `DD_APPLICATION_KEY`. Set `datadog.service` only when it differs from the project's `app_name`; otherwise the agent uses `app_name` as the service filter. Configure `datadog.api.metric_queries` with the actual service metric names when error rate, 4xx/5xx, or P95 data is required.

Set `defaults.time_range` to `today`, `yesterday`, `last_<N>d`, or `last_<N>h` (for example `last_24h`). A project or manual request may override it with the same preset or explicit UTC `start`/`end` timestamps. Datadog and Sentry use exact UTC bounds; Stability SDK uses the calendar-day range covering the window. Tracking patrol always reads the latest run.

Configure the shared Stability SDK run entirely in the root-level `stability_sdk` block. Its `enabled`, `output_mode`, `time_granularity`, `partition_timezone`, and stability-window settings apply to every enabled project; project-level `stability_sdk` blocks are not supported.
