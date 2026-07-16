# Monitoring Core

- Responsibility → planned configuration-driven orchestration and report aggregation.
- Entry Points → `.agents/monitoring-agent.md` → Subagent; `monitoring-agent/SKILL.md` → Skill.
- Key Files → `monitoring-agent/runtime.py` → Sentry and GitHub HTTP adapters; `monitoring-agent/references/contracts.md` → result contract.
- Constraints → parallel paths; independent timeouts; normalized results; no fabricated values.
- Symbols → none yet.

| Layer | Item | Description |
|-------|------|-------------|
| Implementation | `monitoring-agent/` | orchestration skill and adapters |
| Consumer | `.agents/monitoring-agent.md` | thin Subagent wrapper |
