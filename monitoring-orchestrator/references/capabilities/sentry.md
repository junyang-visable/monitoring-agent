# Sentry Capability

## Invocation

Before invocation, merge the root `sentry` block with the project's `sentry` block using `resolve_project_signal_config`; project values override shared values. The root block provides organization, base URL, and token environment variable. The project block provides `enabled`, the Sentry project identifier, and exceptional overrides.

Call the Sentry REST API using the resulting effective configuration.

Pass the resolved UTC monitoring window. Query the immediately preceding, equal-duration window as the baseline.

## Required data

Return the current error count, baseline error count, delta, and the current and baseline windows when available.

## Result handling

Normalize the response to the signal contract in [../contracts.md](../contracts.md). Omit percentage delta when the baseline is zero. Convert missing credentials, HTTP failures, invalid responses, and timeouts into `degraded` or `unavailable` results according to the contract.

The standard-library HTTP implementation is in `monitoring-orchestrator/adapters/sentry.py`.
