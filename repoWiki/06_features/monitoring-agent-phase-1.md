# Monitoring Agent Phase 1

## Overview

Configuration-driven monitoring for multiple projects. The Subagent delegates to a Skill that invokes four real monitoring capabilities and emits normalized reports with evidence.

## Architecture

```mermaid
flowchart LR
    Trigger[Subagent or Cron] --> Config[Project Config]
    Config --> Parallel[Parallel Signal Calls]
    Parallel --> Datadog[Datadog MCP]
    Parallel --> Stability[Stability SDK]
    Parallel --> Sentry[Sentry API]
    Parallel --> Patrol[GitHub Actions]
    Datadog --> Normalize[Normalize and Isolate Failures]
    Stability --> Normalize
    Sentry --> Normalize
    Patrol --> Normalize
    Normalize --> Report[Markdown JSON and Evidence]
```

## Key Files

| File | Role |
|------|------|
| `.agents/monitoring-agent.md` | Thin Subagent entry and no-fabrication contract |
| `monitoring-orchestrator/SKILL.md` | Orchestration sequence and capability whitelist |
| `monitoring-orchestrator/runtime.py` | Real Sentry and GitHub Actions HTTP adapters |
| `monitoring-orchestrator/config/monitoring_config.yaml` | Multi-project non-secret Skill configuration |
| `monitoring-orchestrator/references/contracts.md` | Normalized signal envelope |
| `monitoring-orchestrator/templates/monitoring_report.md.tpl` | Four-signal report layout |

## Implementation Notes

- Four paths run independently; one timeout or exception cannot block other signals.
- Missing credentials produce `unavailable`; metrics remain empty.
- Sentry compares adjacent 24-hour windows and omits percentage delta when baseline is zero.
- Stability SDK always queries the rolling previous 24 hours through `fe-stability-analysis`.
- tracking_patrol reads latest by default; `trigger` is explicit in config or manual override.
- Tokens are read from environment variables and recursively redacted in evidence.
- Datadog and Stability SDK remain agent capability calls; the Python runtime does not fabricate or emulate MCP results.

## Dependencies

- `user-datadog` MCP → Datadog metrics, monitors, and events.
- `fe-stability-analysis` → Stability SDK signal chain.
- Sentry REST API → error counts for two 24-hour windows.
- GitHub Actions API → tracking_patrol workflow runs and dispatch.
- Python standard library → HTTP, JSON, timestamps, and filesystem evidence.
