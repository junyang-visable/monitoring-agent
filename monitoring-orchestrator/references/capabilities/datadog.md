# Datadog Capability

## Invocation

Use the Datadog REST API adapter `fetch_datadog` in `monitoring-orchestrator/adapters/datadog.py`.

Before invocation, merge the root `datadog` block with the project's `datadog` block using `resolve_project_signal_config`; project values override shared values. Keep API connection, credential environment variables, and common query templates in the root block. Keep `enabled`, `service`, and exceptional query overrides in the project block.

The API requires `DD_API_KEY` and `DD_APPLICATION_KEY` (or the environment variable names configured under the root `datadog.api` block).

Pass the resolved UTC `start` and `end` for the shared monitoring window. Resolve the service filter from `datadog.service` when configured; otherwise use the project's `app_name`.

## Required data

- Error rate
- 4xx/5xx responses
- P95 latency
- Monitor state when available
- Relevant events within the resolved time range

The adapter searches error logs and service monitors by default. Configure `metric_queries` with the service's actual Datadog metric names for error rate, 4xx/5xx, and P95 latency. Query templates may use `{service}`.

## Result handling

Normalize the API response to the signal contract in [../contracts.md](../contracts.md). Preserve only values returned by Datadog; do not fabricate missing metrics. Missing credentials, permission errors, HTTP failures, or empty responses must become `degraded` or `unavailable` results according to the contract.
