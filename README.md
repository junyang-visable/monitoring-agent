# Monitoring Agent

Configuration-driven monitoring agent for collecting signals from multiple projects and producing structured reports.

## Usage

1. Configure projects in `monitoring-orchestrator/config/monitoring_config.yaml`.
2. Put service tokens in environment variables referenced by the config.
3. Invoke `.agents/monitoring-agent.md` or load `monitoring-orchestrator/SKILL.md`.
4. Inspect reports and redacted evidence under `artifacts/monitoring/`.

The agent performs real calls only. Missing credentials, permissions, empty responses, and timeouts are reported as degraded or unavailable; no synthetic metrics are generated.
