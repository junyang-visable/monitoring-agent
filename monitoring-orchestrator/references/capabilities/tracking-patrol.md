# Tracking Patrol Capability

## Invocation

Before invocation, merge the root `tracking_patrol` block with the project's `tracking_patrol` block using `resolve_project_signal_config`; project values override shared values. The root block provides owner, repository, token environment variable, and default mode. The project block provides `enabled`, workflow, and exceptional overrides.

Use the GitHub Actions API with the resulting effective configuration.

By default, read the latest workflow run. Dispatch a new run only when `mode` is `trigger` or a manual override explicitly requests it. Do not apply the shared monitoring `time_range` to this signal.

## Result handling

Return the latest run status, conclusion, run identifier, and URL when available. Normalize the response to the signal contract in [../contracts.md](../contracts.md).

The standard-library HTTP implementation is in `monitoring-orchestrator/adapters/github.py`.
