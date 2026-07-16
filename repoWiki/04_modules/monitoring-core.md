# Monitoring Core

- Responsibility → planned configuration-driven orchestration and report aggregation.
- Entry Points → `.agents/monitoring-agent.md` → Subagent; `monitoring-orchestrator/SKILL.md` → Skill.
- Key Files → `monitoring-orchestrator/runtime.py` → Sentry and GitHub HTTP adapters; `monitoring-orchestrator/references/contracts.md` → result contract.
- Constraints → parallel paths; independent timeouts; normalized results; no fabricated values.
- Symbols → none yet.

| Layer | Item | Description |
|-------|------|-------------|
| Implementation | `monitoring-orchestrator/` | orchestration skill and adapters |
| Consumer | `.agents/monitoring-agent.md` | thin Subagent wrapper |
