# Monitoring Core

- Responsibility → configuration-driven orchestration, signal normalization, and report aggregation.
- Entry Points → `.agents/monitoring-agent.md` → Subagent; `monitoring-orchestrator/SKILL.md` → Skill.
- Key Files → `monitoring-orchestrator/runtime.py` → Sentry and GitHub HTTP adapters; `monitoring-orchestrator/references/contracts.md` → result contract.
- Constraints → parallel paths; independent timeouts; normalized results; no fabricated values; every run uses one UTC `run_id` in `YYYYMMDDTHHMMSSZ` format; Datadog service override falls back to `app_name`; Datadog, Stability SDK, and Sentry inherit a shared `time_range`; Stability SDK batches enabled projects by `app_name` and writes its analysis JSON to `artifacts/fe-stability-analysis/<run_id>/`.
- Symbols → none yet.

| Layer | Item | Description |
|-------|------|-------------|
| Implementation | `monitoring-orchestrator/` | orchestration skill and adapters |
| Consumer | `.agents/monitoring-agent.md` | thin Subagent wrapper |
