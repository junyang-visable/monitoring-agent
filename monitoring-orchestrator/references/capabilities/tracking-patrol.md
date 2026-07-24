# Tracking Patrol Capability

## Invocation

Use the GitHub Actions API for the configured owner, repository, workflow, and token environment variable.

By default, read the latest workflow run. Dispatch a new run only when `mode` is `trigger` or a manual override explicitly requests it. Do not apply the shared monitoring `time_range` to this signal.

## Result handling

Return the latest run status, conclusion, run identifier, and URL when available. Normalize the response to the signal contract in [../contracts.md](../contracts.md).

The standard-library HTTP implementation is in `monitoring-orchestrator/adapters/github.py`.
