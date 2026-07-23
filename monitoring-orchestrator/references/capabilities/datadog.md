# Datadog Capability

## Invocation

Invoke the configured `user-datadog` MCP capability for metrics, monitors, and events.

Pass the resolved UTC `start` and `end` for the shared monitoring window. Resolve the service filter from `datadog.service` when configured; otherwise use the project's `app_name`.

## Required data

- Error rate
- 4xx/5xx responses
- P95 latency
- Monitor state when available
- Relevant events within the resolved time range

## Result handling

Normalize the capability response to the signal contract in [../contracts.md](../contracts.md). Preserve only values returned by Datadog; do not fabricate missing metrics. If the MCP capability cannot be invoked, record an `unavailable` result and continue the other paths.

