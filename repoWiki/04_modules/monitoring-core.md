# Monitoring Core

- Responsibility → configuration-driven orchestration, signal normalization, and report aggregation.
- Entry Points → `.agents/monitoring-agent.md` → Subagent; `monitoring-orchestrator/SKILL.md` → Skill.
- Key Files → `monitoring-orchestrator/runtime.py` → Sentry and GitHub HTTP adapters; `monitoring-orchestrator/references/contracts.md` → result contract.
- Constraints → parallel paths; independent timeouts; normalized results; no fabricated values; every run uses one UTC `run_id` in `YYYYMMDDTHHMMSSZ` format; Datadog service override falls back to `app_name`; Datadog, Stability SDK, and Sentry inherit a shared `time_range`; Stability SDK batches enabled projects by `app_name` and writes its overview to `artifacts/monitoring/<run_id>/overview.json` and each project result to that project's directory.
- Symbols → none yet.

| Layer | Item | Description |
|-------|------|-------------|
| Implementation | `monitoring-orchestrator/` | orchestration skill and adapters |
| Consumer | `.agents/monitoring-agent.md` | thin Subagent wrapper |
