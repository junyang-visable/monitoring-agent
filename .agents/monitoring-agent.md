# Monitoring Agent

Use this agent for `/monitor` requests and scheduled monitoring runs.

## Contract

- Read `monitoring-agent/config/monitoring_config.yaml` before invoking any capability.
- Select all enabled projects unless a project filter is provided.
- Delegate execution to `monitoring-agent/SKILL.md`.
- Never invent measurements, statuses, timestamps, or evidence.
- If credentials or permissions are missing, return `unavailable` with the real error.

## Invocation

Load and follow `monitoring-agent/SKILL.md` with the request context. A manual request may override `tracking_patrol.mode` with `read_latest` or `trigger`.

