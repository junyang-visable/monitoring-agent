# Datadog Capability

## Invocation

Use the Datadog REST API adapter `fetch_datadog` in `monitoring-orchestrator/adapters/datadog.py`.

Before invocation, merge the root `datadog` block with the project's `datadog` block using `resolve_project_signal_config`; project values override shared values. Keep API connection, credential environment variables, and common query templates in the root block. Keep `enabled`, `service`, and exceptional query overrides in the project block.

The API requires `DD_API_KEY` and `DD_APPLICATION_KEY` (or the environment variable names configured under the root `datadog.api` block).

Pass the resolved UTC `start` and `end` for the shared monitoring window. Resolve the service filter from `datadog.service` when configured; otherwise use the project's `app_name`.

## Required data

- Total error-log count within the resolved time range
- Top five errors by count
- Monitor state when available
- Configured metric queries such as error rate, 4xx/5xx, and P95 latency when available

The adapter uses the Logs Aggregate API twice: one total `count` query and one grouped `count` query sorted descending with `top_error_limit=5`. Configure `error_group_by` with a Datadog log facet such as `@error.message`. Configure `metric_queries` with the service's actual Datadog metric names for error rate, 4xx/5xx, and P95 latency. Query templates may use `{service}`.

## Result handling

Normalize the API response to the signal contract in [../contracts.md](../contracts.md). Preserve only values returned by Datadog; do not fabricate missing metrics. Missing credentials, permission errors, HTTP failures, or empty responses must become `degraded` or `unavailable` results according to the contract.

The normalized Datadog metrics include:

```yaml
error_log_count: integer
top_errors:
  - rank: integer
    error: string
    count: integer
dominant_error: string | null
dominant_error_count: integer
monitors: []
metric_queries: {}
```
